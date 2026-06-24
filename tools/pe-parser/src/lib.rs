use serde::Serialize;
use std::fs::File;
use std::io::Read;
use std::path::Path;

pub mod api_index;

#[derive(Serialize, Clone)]
pub struct Section {
    pub name: String,
    pub vaddr: u32,
    pub vsize: u32,
    pub raddr: u32,
    pub rsize: u32,
    pub chars: u32,
    pub exec: bool,
}

#[derive(Serialize, Clone)]
pub struct Export {
    pub name: String,
    pub rva: u32,
    pub ordinal: u32,
    pub forwarder: Option<String>,
}

#[derive(Serialize, Clone)]
pub struct ParsedPE {
    pub pe64: bool,
    pub machine: u16,
    pub image_base: u64,
    pub entry_rva: u32,
    pub import_dir: (u32, u32),
    pub export_dir: (u32, u32),
    pub sections: Vec<Section>,
    pub imports: Vec<String>,
    pub exports: Vec<Export>,
}

pub fn read_u16(data: &[u8], off: usize) -> Option<u16> {
    if off + 2 <= data.len() {
        Some(u16::from_le_bytes([data[off], data[off + 1]]))
    } else {
        None
    }
}

pub fn read_u32(data: &[u8], off: usize) -> Option<u32> {
    if off + 4 <= data.len() {
        Some(u32::from_le_bytes([
            data[off],
            data[off + 1],
            data[off + 2],
            data[off + 3],
        ]))
    } else {
        None
    }
}

pub fn read_u64(data: &[u8], off: usize) -> Option<u64> {
    if off + 8 <= data.len() {
        Some(u64::from_le_bytes([
            data[off],
            data[off + 1],
            data[off + 2],
            data[off + 3],
            data[off + 4],
            data[off + 5],
            data[off + 6],
            data[off + 7],
        ]))
    } else {
        None
    }
}

pub fn rva_to_off(rva: u32, sections: &[Section]) -> Option<usize> {
    for sec in sections {
        let max_size = std::cmp::max(sec.vsize, sec.rsize);
        if rva >= sec.vaddr && rva < sec.vaddr + max_size {
            return Some((rva - sec.vaddr + sec.raddr) as usize);
        }
    }
    None
}

pub fn read_cstr(data: &[u8], off: usize, maxlen: usize) -> String {
    if off >= data.len() {
        return String::new();
    }
    let end = data[off..]
        .iter()
        .take(maxlen)
        .position(|&b| b == 0)
        .map(|pos| off + pos)
        .unwrap_or_else(|| std::cmp::min(off + maxlen, data.len()));
    String::from_utf8_lossy(&data[off..end]).into_owned()
}

pub fn parse_pe_bytes(data: &[u8]) -> Result<ParsedPE, String> {
    if data.len() < 4 {
        return Err("truncated file".to_string());
    }

    if &data[0..2] == b"MZ" {
        return parse_mz_pe(data);
    }

    if &data[0..4] == b"\x7fELF" {
        return parse_elf(data);
    }

    let magic = u32::from_le_bytes(data[0..4].try_into().unwrap());
    if magic == 0xFEEDFACE || magic == 0xFEEDFACF || magic == 0xCEFAEDFE || magic == 0xCFFAEDFE {
        return parse_macho(data);
    }

    Err("unsupported binary format: magic does not match PE, ELF, or Mach-O".to_string())
}

fn parse_mz_pe(data: &[u8]) -> Result<ParsedPE, String> {
    let pe_off = read_u32(data, 0x3C).ok_or("invalid PE offset")? as usize;
    if pe_off + 4 > data.len() || &data[pe_off..pe_off + 4] != b"PE\x00\x00" {
        return Err("not a PE: missing PE signature".to_string());
    }

    let coff = pe_off + 4;
    let machine = read_u16(data, coff).ok_or("missing machine type")?;
    let num_sections = read_u16(data, coff + 2).ok_or("missing section count")?;
    let opt_size = read_u16(data, coff + 16).ok_or("missing optional header size")?;
    let opt_off = coff + 20;

    if opt_off + 2 > data.len() {
        return Err("truncated optional header magic".to_string());
    }
    let magic = read_u16(data, opt_off).ok_or("missing optional header magic")?;
    let pe64 = magic == 0x20B;

    let entry_rva = read_u32(data, opt_off + 16).unwrap_or(0);
    let image_base = if pe64 {
        read_u64(data, opt_off + 24).unwrap_or(0)
    } else {
        read_u32(data, opt_off + 28).unwrap_or(0) as u64
    };

    let dd_off = opt_off + if pe64 { 112 } else { 96 };
    let export_dir = (
        read_u32(data, dd_off).unwrap_or(0),
        read_u32(data, dd_off + 4).unwrap_or(0),
    );
    let import_dir = (
        read_u32(data, dd_off + 8).unwrap_or(0),
        read_u32(data, dd_off + 12).unwrap_or(0),
    );

    let sec_off = opt_off + opt_size as usize;
    let mut sections = Vec::new();
    for i in 0..num_sections as usize {
        let s = sec_off + i * 40;
        if s + 40 > data.len() {
            break;
        }
        let name_bytes = &data[s..s + 8];
        let name_len = name_bytes.iter().position(|&b| b == 0).unwrap_or(8);
        let name = String::from_utf8_lossy(&name_bytes[..name_len]).into_owned();

        let vsize = read_u32(data, s + 8).unwrap_or(0);
        let vaddr = read_u32(data, s + 12).unwrap_or(0);
        let rsize = read_u32(data, s + 16).unwrap_or(0);
        let raddr = read_u32(data, s + 20).unwrap_or(0);
        let chars = read_u32(data, s + 36).unwrap_or(0);
        let exec = (chars & 0x20000000) != 0;

        sections.push(Section {
            name,
            vaddr,
            vsize,
            raddr,
            rsize,
            chars,
            exec,
        });
    }

    let mut imports = Vec::new();
    if import_dir.0 > 0 {
        if let Some(import_foff) = rva_to_off(import_dir.0, &sections) {
            let mut off = import_foff;
            let ptr_sz = if pe64 { 8 } else { 4 };
            let ord_bit = if pe64 { 0x8000000000000000 } else { 0x80000000 };

            while off + 20 <= data.len() {
                let oft = read_u32(data, off).unwrap_or(0);
                let name_rva = read_u32(data, off + 12).unwrap_or(0);
                let ft = read_u32(data, off + 16).unwrap_or(0);

                if oft == 0 && name_rva == 0 && ft == 0 {
                    break;
                }

                let dll_off = if name_rva > 0 {
                    rva_to_off(name_rva, &sections)
                } else {
                    None
                };
                let dll_name = if let Some(doff) = dll_off {
                    read_cstr(data, doff, 256)
                } else {
                    String::new()
                };

                let thunk_rva = if oft > 0 { oft } else { ft };
                if let Some(mut thunk_off) = rva_to_off(thunk_rva, &sections) {
                    while thunk_off + ptr_sz <= data.len() {
                        let t = if pe64 {
                            read_u64(data, thunk_off).unwrap_or(0)
                        } else {
                            read_u32(data, thunk_off).unwrap_or(0) as u64
                        };
                        if t == 0 {
                            break;
                        }
                        if (t & ord_bit) == 0 {
                            let ibn_rva = (t & 0xFFFFFFFF) as u32;
                            if let Some(ibn_off) = rva_to_off(ibn_rva, &sections) {
                                let func_name = read_cstr(data, ibn_off + 2, 256);
                                if !func_name.is_empty() && !dll_name.is_empty() {
                                    imports.push(format!(
                                        "{}!{}",
                                        dll_name.to_lowercase(),
                                        func_name
                                    ));
                                }
                            }
                        }
                        thunk_off += ptr_sz;
                    }
                }
                off += 20;
            }
        }
    }

    let mut exports = Vec::new();
    if export_dir.0 > 0 {
        if let Some(exp_off) = rva_to_off(export_dir.0, &sections) {
            let ord_base = read_u32(data, exp_off + 16).unwrap_or(0);
            let num_func = read_u32(data, exp_off + 20).unwrap_or(0) as usize;
            let num_name = read_u32(data, exp_off + 24).unwrap_or(0) as usize;
            let eat_rva = read_u32(data, exp_off + 28).unwrap_or(0);
            let ent_rva = read_u32(data, exp_off + 32).unwrap_or(0);
            let ot_rva = read_u32(data, exp_off + 36).unwrap_or(0);

            let eat_off = rva_to_off(eat_rva, &sections);
            let ent_off = rva_to_off(ent_rva, &sections);
            let ot_off = rva_to_off(ot_rva, &sections);

            let mut names_map = std::collections::HashMap::new();
            if let (Some(ent), Some(ot)) = (ent_off, ot_off) {
                for i in 0..num_name {
                    let n_rva_off = ent + i * 4;
                    let ord_off = ot + i * 2;
                    if n_rva_off + 4 <= data.len() && ord_off + 2 <= data.len() {
                        let name_rva = read_u32(data, n_rva_off).unwrap_or(0);
                        let ord = read_u16(data, ord_off).unwrap_or(0) as u32;
                        if let Some(n_off) = rva_to_off(name_rva, &sections) {
                            let name = read_cstr(data, n_off, 256);
                            names_map.insert(ord, name);
                        }
                    }
                }
            }

            if let Some(eat) = eat_off {
                for i in 0..num_func {
                    let func_rva_off = eat + i * 4;
                    if func_rva_off + 4 <= data.len() {
                        let func_rva = read_u32(data, func_rva_off).unwrap_or(0);
                        if func_rva == 0 {
                            continue;
                        }

                        let name = names_map
                            .get(&(i as u32))
                            .cloned()
                            .unwrap_or_else(|| format!("Ordinal{}", ord_base + i as u32));

                        let is_forwarder =
                            func_rva >= export_dir.0 && func_rva < export_dir.0 + export_dir.1;
                        let forwarder = if is_forwarder {
                            rva_to_off(func_rva, &sections).map(|foff| read_cstr(data, foff, 512))
                        } else {
                            None
                        };

                        exports.push(Export {
                            name,
                            rva: func_rva,
                            ordinal: ord_base + i as u32,
                            forwarder,
                        });
                    }
                }
            }
        }
    }

    Ok(ParsedPE {
        pe64,
        machine,
        image_base,
        entry_rva,
        import_dir,
        export_dir,
        sections,
        imports,
        exports,
    })
}

fn parse_elf(data: &[u8]) -> Result<ParsedPE, String> {
    if data.len() < 64 {
        return Err("truncated ELF header".to_string());
    }
    let class = data[4];
    let pe64 = class == 2;
    let is_lsb = data[5] == 1;

    let machine = if is_lsb {
        u16::from_le_bytes([data[18], data[19]])
    } else {
        u16::from_be_bytes([data[18], data[19]])
    };

    let (shoff, shentsize, shnum, shstrndx) = if pe64 {
        if is_lsb {
            let shoff = u64::from_le_bytes(data[40..48].try_into().unwrap()) as usize;
            let shentsize = u16::from_le_bytes(data[58..60].try_into().unwrap()) as usize;
            let shnum = u16::from_le_bytes(data[60..62].try_into().unwrap()) as usize;
            let shstrndx = u16::from_le_bytes(data[62..64].try_into().unwrap()) as usize;
            (shoff, shentsize, shnum, shstrndx)
        } else {
            let shoff = u64::from_be_bytes(data[40..48].try_into().unwrap()) as usize;
            let shentsize = u16::from_be_bytes(data[58..60].try_into().unwrap()) as usize;
            let shnum = u16::from_be_bytes(data[60..62].try_into().unwrap()) as usize;
            let shstrndx = u16::from_be_bytes(data[62..64].try_into().unwrap()) as usize;
            (shoff, shentsize, shnum, shstrndx)
        }
    } else {
        if is_lsb {
            let shoff = u32::from_le_bytes(data[32..36].try_into().unwrap()) as usize;
            let shentsize = u16::from_le_bytes(data[46..48].try_into().unwrap()) as usize;
            let shnum = u16::from_le_bytes(data[48..50].try_into().unwrap()) as usize;
            let shstrndx = u16::from_le_bytes(data[50..52].try_into().unwrap()) as usize;
            (shoff, shentsize, shnum, shstrndx)
        } else {
            let shoff = u32::from_be_bytes(data[32..36].try_into().unwrap()) as usize;
            let shentsize = u16::from_be_bytes(data[46..48].try_into().unwrap()) as usize;
            let shnum = u16::from_be_bytes(data[48..50].try_into().unwrap()) as usize;
            let shstrndx = u16::from_be_bytes(data[50..52].try_into().unwrap()) as usize;
            (shoff, shentsize, shnum, shstrndx)
        }
    };

    if shoff == 0 || shnum == 0 || shoff + shnum * shentsize > data.len() {
        return Err("invalid ELF section header table".to_string());
    }

    let shstrtab_sec_off = shoff + shstrndx * shentsize;
    let (shstr_off, shstr_size) = if pe64 {
        if is_lsb {
            let off = u64::from_le_bytes(
                data[shstrtab_sec_off + 24..shstrtab_sec_off + 32]
                    .try_into()
                    .unwrap(),
            ) as usize;
            let sz = u64::from_le_bytes(
                data[shstrtab_sec_off + 32..shstrtab_sec_off + 40]
                    .try_into()
                    .unwrap(),
            ) as usize;
            (off, sz)
        } else {
            let off = u64::from_be_bytes(
                data[shstrtab_sec_off + 24..shstrtab_sec_off + 32]
                    .try_into()
                    .unwrap(),
            ) as usize;
            let sz = u64::from_be_bytes(
                data[shstrtab_sec_off + 32..shstrtab_sec_off + 40]
                    .try_into()
                    .unwrap(),
            ) as usize;
            (off, sz)
        }
    } else {
        if is_lsb {
            let off = u32::from_le_bytes(
                data[shstrtab_sec_off + 16..shstrtab_sec_off + 20]
                    .try_into()
                    .unwrap(),
            ) as usize;
            let sz = u32::from_le_bytes(
                data[shstrtab_sec_off + 20..shstrtab_sec_off + 24]
                    .try_into()
                    .unwrap(),
            ) as usize;
            (off, sz)
        } else {
            let off = u32::from_be_bytes(
                data[shstrtab_sec_off + 16..shstrtab_sec_off + 20]
                    .try_into()
                    .unwrap(),
            ) as usize;
            let sz = u32::from_be_bytes(
                data[shstrtab_sec_off + 20..shstrtab_sec_off + 24]
                    .try_into()
                    .unwrap(),
            ) as usize;
            (off, sz)
        }
    };

    if shstr_off + shstr_size > data.len() {
        return Err("invalid shstrtab offset/size".to_string());
    }
    let shstrtab = &data[shstr_off..shstr_off + shstr_size];

    let mut sections = Vec::new();
    for i in 0..shnum {
        let entry_off = shoff + i * shentsize;
        if entry_off + shentsize > data.len() {
            break;
        }
        let (sh_name_idx, sh_type, sh_flags, sh_addr, sh_offset, sh_size) = if pe64 {
            if is_lsb {
                let name =
                    u32::from_le_bytes(data[entry_off..entry_off + 4].try_into().unwrap()) as usize;
                let typ =
                    u32::from_le_bytes(data[entry_off + 4..entry_off + 8].try_into().unwrap());
                let flags =
                    u64::from_le_bytes(data[entry_off + 8..entry_off + 16].try_into().unwrap());
                let addr =
                    u64::from_le_bytes(data[entry_off + 16..entry_off + 24].try_into().unwrap());
                let offset =
                    u64::from_le_bytes(data[entry_off + 24..entry_off + 32].try_into().unwrap())
                        as usize;
                let size =
                    u64::from_le_bytes(data[entry_off + 32..entry_off + 40].try_into().unwrap())
                        as usize;
                (name, typ, flags, addr, offset, size)
            } else {
                let name =
                    u32::from_be_bytes(data[entry_off..entry_off + 4].try_into().unwrap()) as usize;
                let typ =
                    u32::from_be_bytes(data[entry_off + 4..entry_off + 8].try_into().unwrap());
                let flags =
                    u64::from_be_bytes(data[entry_off + 8..entry_off + 16].try_into().unwrap());
                let addr =
                    u64::from_be_bytes(data[entry_off + 16..entry_off + 24].try_into().unwrap());
                let offset =
                    u64::from_be_bytes(data[entry_off + 24..entry_off + 32].try_into().unwrap())
                        as usize;
                let size =
                    u64::from_be_bytes(data[entry_off + 32..entry_off + 40].try_into().unwrap())
                        as usize;
                (name, typ, flags, addr, offset, size)
            }
        } else {
            if is_lsb {
                let name =
                    u32::from_le_bytes(data[entry_off..entry_off + 4].try_into().unwrap()) as usize;
                let typ =
                    u32::from_le_bytes(data[entry_off + 4..entry_off + 8].try_into().unwrap());
                let flags =
                    u32::from_le_bytes(data[entry_off + 8..entry_off + 12].try_into().unwrap())
                        as u64;
                let addr =
                    u32::from_le_bytes(data[entry_off + 12..entry_off + 16].try_into().unwrap())
                        as u64;
                let offset =
                    u32::from_le_bytes(data[entry_off + 16..entry_off + 20].try_into().unwrap())
                        as usize;
                let size =
                    u32::from_le_bytes(data[entry_off + 20..entry_off + 24].try_into().unwrap())
                        as usize;
                (name, typ, flags, addr, offset, size)
            } else {
                let name =
                    u32::from_be_bytes(data[entry_off..entry_off + 4].try_into().unwrap()) as usize;
                let typ =
                    u32::from_be_bytes(data[entry_off + 4..entry_off + 8].try_into().unwrap());
                let flags =
                    u32::from_be_bytes(data[entry_off + 8..entry_off + 12].try_into().unwrap())
                        as u64;
                let addr =
                    u32::from_be_bytes(data[entry_off + 12..entry_off + 16].try_into().unwrap())
                        as u64;
                let offset =
                    u32::from_be_bytes(data[entry_off + 16..entry_off + 20].try_into().unwrap())
                        as usize;
                let size =
                    u32::from_be_bytes(data[entry_off + 20..entry_off + 24].try_into().unwrap())
                        as usize;
                (name, typ, flags, addr, offset, size)
            }
        };

        if sh_type != 0 && sh_size > 0 {
            let end = shstrtab[sh_name_idx..]
                .iter()
                .position(|&b| b == 0)
                .map(|p| sh_name_idx + p)
                .unwrap_or(shstrtab.len());
            let name = String::from_utf8_lossy(&shstrtab[sh_name_idx..end]).into_owned();
            let exec = (sh_flags & 0x4) != 0;
            let chars = if exec { 0x60000020 } else { 0x40000040 };

            sections.push(Section {
                name,
                vaddr: sh_addr as u32,
                vsize: sh_size as u32,
                raddr: sh_offset as u32,
                rsize: sh_size as u32,
                chars,
                exec,
            });
        }
    }

    Ok(ParsedPE {
        pe64,
        machine,
        image_base: 0,
        entry_rva: 0,
        import_dir: (0, 0),
        export_dir: (0, 0),
        sections,
        imports: Vec::new(),
        exports: Vec::new(),
    })
}

fn parse_macho(data: &[u8]) -> Result<ParsedPE, String> {
    if data.len() < 32 {
        return Err("truncated Mach-O header".to_string());
    }
    let magic = u32::from_le_bytes(data[0..4].try_into().unwrap());
    let (pe64, is_lsb) = match magic {
        0xFEEDFACE => (false, true),
        0xFEEDFACF => (true, true),
        0xCEFAEDFE => (false, false),
        0xCFFAEDFE => (true, false),
        _ => return Err("invalid Mach-O magic".to_string()),
    };

    let read_u32_endian = |offset: usize| -> Option<u32> {
        if offset + 4 <= data.len() {
            let b = [
                data[offset],
                data[offset + 1],
                data[offset + 2],
                data[offset + 3],
            ];
            if is_lsb {
                Some(u32::from_le_bytes(b))
            } else {
                Some(u32::from_be_bytes(b))
            }
        } else {
            None
        }
    };

    let read_u64_endian = |offset: usize| -> Option<u64> {
        if offset + 8 <= data.len() {
            let b = [
                data[offset],
                data[offset + 1],
                data[offset + 2],
                data[offset + 3],
                data[offset + 4],
                data[offset + 5],
                data[offset + 6],
                data[offset + 7],
            ];
            if is_lsb {
                Some(u64::from_le_bytes(b))
            } else {
                Some(u64::from_be_bytes(b))
            }
        } else {
            None
        }
    };

    let ncmds = read_u32_endian(16).ok_or("missing load command count")? as usize;
    let mut off = if pe64 { 32 } else { 28 };

    let mut sections = Vec::new();
    for _ in 0..ncmds {
        if off + 8 > data.len() {
            break;
        }
        let cmd = read_u32_endian(off).unwrap();
        let cmdsize = read_u32_endian(off + 4).unwrap() as usize;
        if off + cmdsize > data.len() {
            break;
        }

        if cmd == 0x19 && pe64 {
            let nsects = read_u32_endian(off + 64).unwrap_or(0) as usize;
            let mut sect_off = off + 72;
            for _ in 0..nsects {
                if sect_off + 80 > data.len() {
                    break;
                }
                let name_bytes = &data[sect_off..sect_off + 16];
                let name_len = name_bytes.iter().position(|&b| b == 0).unwrap_or(16);
                let name = String::from_utf8_lossy(&name_bytes[..name_len]).into_owned();

                let addr = read_u64_endian(sect_off + 32).unwrap_or(0);
                let size = read_u64_endian(sect_off + 40).unwrap_or(0);
                let offset = read_u32_endian(sect_off + 48).unwrap_or(0);
                let flags = read_u32_endian(sect_off + 60).unwrap_or(0);

                let exec = (flags & 0x80000000) != 0 || name == "__text";
                let chars = if exec { 0x60000020 } else { 0x40000040 };

                sections.push(Section {
                    name,
                    vaddr: addr as u32,
                    vsize: size as u32,
                    raddr: offset,
                    rsize: size as u32,
                    chars,
                    exec,
                });
                sect_off += 80;
            }
        } else if cmd == 0x1 && !pe64 {
            let nsects = read_u32_endian(off + 48).unwrap_or(0) as usize;
            let mut sect_off = off + 56;
            for _ in 0..nsects {
                if sect_off + 68 > data.len() {
                    break;
                }
                let name_bytes = &data[sect_off..sect_off + 16];
                let name_len = name_bytes.iter().position(|&b| b == 0).unwrap_or(16);
                let name = String::from_utf8_lossy(&name_bytes[..name_len]).into_owned();

                let addr = read_u32_endian(sect_off + 24).unwrap_or(0);
                let size = read_u32_endian(sect_off + 28).unwrap_or(0);
                let offset = read_u32_endian(sect_off + 32).unwrap_or(0);
                let flags = read_u32_endian(sect_off + 48).unwrap_or(0);

                let exec = (flags & 0x80000000) != 0 || name == "__text";
                let chars = if exec { 0x60000020 } else { 0x40000040 };

                sections.push(Section {
                    name,
                    vaddr: addr,
                    vsize: size,
                    raddr: offset,
                    rsize: size,
                    chars,
                    exec,
                });
                sect_off += 68;
            }
        }
        off += cmdsize;
    }

    Ok(ParsedPE {
        pe64,
        machine: 0,
        image_base: 0,
        entry_rva: 0,
        import_dir: (0, 0),
        export_dir: (0, 0),
        sections,
        imports: Vec::new(),
        exports: Vec::new(),
    })
}

pub fn load_binary_data(path: &Path) -> Result<Vec<u8>, String> {
    let mut file = File::open(path).map_err(|e| format!("Could not open file: {}", e))?;
    let mut data = Vec::new();
    file.read_to_end(&mut data)
        .map_err(|e| format!("Could not read file: {}", e))?;
    Ok(data)
}

pub fn parse_byte_pattern(text: &str) -> Result<Vec<Option<u8>>, String> {
    let mut out = Vec::new();
    for tok in text.replace(',', " ").split_whitespace() {
        if tok == "?" || tok == "??" {
            out.push(None);
            continue;
        }
        if tok.len() != 2 {
            return Err(format!("invalid hex byte {tok:?}"));
        }
        let byte = u8::from_str_radix(tok, 16).map_err(|_| format!("invalid hex byte {tok:?}"))?;
        out.push(Some(byte));
    }
    if out.is_empty() {
        return Err("empty pattern".to_string());
    }
    Ok(out)
}

pub fn format_byte_pattern(pattern: &[Option<u8>]) -> String {
    pattern
        .iter()
        .map(|b| match b {
            Some(v) => format!("{v:02X}"),
            None => "??".to_string(),
        })
        .collect::<Vec<_>>()
        .join(" ")
}

pub fn scan_pattern(buf: &[u8], pattern: &[Option<u8>]) -> Vec<usize> {
    let n = buf.len();
    let m = pattern.len();
    if m == 0 || m > n {
        return Vec::new();
    }
    let anchor = pattern.iter().position(|b| b.is_some());
    if anchor.is_none() {
        return (0..=n - m).collect();
    }
    let anchor = anchor.unwrap();
    let anchor_byte = pattern[anchor].unwrap();
    let fixed: Vec<(usize, u8)> = pattern
        .iter()
        .enumerate()
        .filter_map(|(idx, b)| b.map(|v| (idx, v)))
        .collect();
    let mut hits = Vec::new();
    let mut pos = anchor;
    while pos < n {
        let rel = match buf[pos..].iter().position(|&b| b == anchor_byte) {
            Some(p) => p,
            None => break,
        };
        pos += rel;
        if pos < anchor {
            pos += 1;
            continue;
        }
        let start = pos - anchor;
        if start + m > n {
            break;
        }
        if fixed.iter().all(|(idx, byte)| buf[start + idx] == *byte) {
            hits.push(start);
        }
        pos += 1;
    }
    hits
}

pub fn section_data<'a>(data: &'a [u8], section: &Section) -> &'a [u8] {
    let start = section.raddr as usize;
    let end = start.saturating_add(section.rsize as usize).min(data.len());
    if start >= data.len() || start >= end {
        &[]
    } else {
        &data[start..end]
    }
}
