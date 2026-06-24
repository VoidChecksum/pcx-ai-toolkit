use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum McpParamKind {
    HexAddress,
    HexHandle,
    HexBytes,
    String,
    Integer,
    Boolean,
    Array,
    Enum(&'static [&'static str]),
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct McpParam {
    pub name: &'static str,
    pub required: bool,
    pub kind: McpParamKind,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct McpTool {
    pub name: &'static str,
    pub takes_handle: bool,
    pub params: &'static [McpParam],
    pub notes: &'static [&'static str],
}
pub struct McpError;
impl McpError {
    pub const PARSE_ERROR: i32 = -32700;
    pub const INVALID_REQUEST: i32 = -32600;
    pub const METHOD_NOT_FOUND: i32 = -32601;
    pub const INVALID_PARAMS: i32 = -32602;
    pub const INTERNAL: i32 = -32603;
    pub const PERMISSION_DENIED: i32 = -32001;
    pub const STALE_HANDLE: i32 = -32002;
    pub const TARGET_NOT_FOUND: i32 = -32003;
    pub const OPERATION_FAILED: i32 = -32004;
}
const NO_PARAMS: &[McpParam] = &[];
const NO_NOTES: &[&str] = &[];
const READ_VIRTUAL_MEMORY_PARAMS: &[McpParam] = &[
    McpParam {
        name: "address",
        required: true,
        kind: McpParamKind::HexAddress,
    },
    McpParam {
        name: "size",
        required: true,
        kind: McpParamKind::Integer,
    },
];
const DEREFERENCE_PARAMS: &[McpParam] = &[McpParam {
    name: "handle",
    required: true,
    kind: McpParamKind::HexHandle,
}];
const FIND_STRING_REFS_PARAMS: &[McpParam] = &[
    McpParam {
        name: "module_base",
        required: true,
        kind: McpParamKind::HexAddress,
    },
    McpParam {
        name: "text",
        required: true,
        kind: McpParamKind::String,
    },
    McpParam {
        name: "encoding",
        required: false,
        kind: McpParamKind::Enum(&["ascii", "utf16"]),
    },
    McpParam {
        name: "heap_only",
        required: false,
        kind: McpParamKind::Boolean,
    },
    McpParam {
        name: "string_module",
        required: false,
        kind: McpParamKind::HexAddress,
    },
];
const SCAN_VALUE_PARAMS: &[McpParam] = &[
    McpParam {
        name: "type",
        required: true,
        kind: McpParamKind::Enum(&[
            "u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "f32", "f64",
        ]),
    },
    McpParam {
        name: "value",
        required: true,
        kind: McpParamKind::String,
    },
    McpParam {
        name: "aligned",
        required: false,
        kind: McpParamKind::Boolean,
    },
    McpParam {
        name: "heap_only",
        required: false,
        kind: McpParamKind::Boolean,
    },
];
macro_rules! tool {
    ($name:literal) => {
        McpTool {
            name: $name,
            takes_handle: true,
            params: NO_PARAMS,
            notes: NO_NOTES,
        }
    };
    (no_handle $name:literal) => {
        McpTool {
            name: $name,
            takes_handle: false,
            params: NO_PARAMS,
            notes: NO_NOTES,
        }
    };
}
pub const TOOLS: &[McpTool] = &[
    tool!(no_handle "process/list"),
    tool!(no_handle "process/info_by_pid"),
    tool!(no_handle "process/info_by_name"),
    tool!(no_handle "process/reference_by_pid"),
    tool!(no_handle "process/reference_by_name"),
    McpTool {
        name: "process/dereference",
        takes_handle: false,
        params: DEREFERENCE_PARAMS,
        notes: NO_NOTES,
    },
    tool!(no_handle "process/cleanup_references"),
    tool!(no_handle "process/list_references"),
    McpTool {
        name: "process/read_virtual_memory",
        takes_handle: true,
        params: READ_VIRTUAL_MEMORY_PARAMS,
        notes: &["max_size=16MiB"],
    },
    tool!("process/write_virtual_memory"),
    tool!("process/is_valid_address"),
    tool!("process/read_typed_value"),
    tool!("process/write_typed_value"),
    tool!("process/read_string"),
    tool!("process/write_string"),
    McpTool {
        name: "process/copy_memory",
        takes_handle: true,
        params: NO_PARAMS,
        notes: &["max_size=64MiB", "chunk_size=1MiB"],
    },
    tool!("process/fill_memory"),
    tool!("process/read_pointer_chain"),
    tool!("process/disassemble"),
    tool!("process/get_modules"),
    tool!("process/get_threads"),
    tool!("process/get_module_by_name"),
    tool!("process/get_export_address"),
    tool!("process/get_import_address"),
    tool!("process/get_module_imports"),
    tool!("process/list_module_exports"),
    tool!("process/get_module_sections"),
    tool!("process/get_pe_header"),
    tool!("process/get_module_strings"),
    tool!("process/get_exception_table"),
    tool!("process/get_data_directory"),
    tool!("process/query_memory_region"),
    tool!("process/enumerate_memory_regions"),
    McpTool {
        name: "process/allocate_memory",
        takes_handle: true,
        params: NO_PARAMS,
        notes: &["max_size=256MiB", "permission=virtual_memory_operations"],
    },
    tool!("process/free_memory"),
    tool!("process/find_pattern"),
    McpTool {
        name: "process/find_all_patterns",
        takes_handle: true,
        params: NO_PARAMS,
        notes: &["cap=1024"],
    },
    McpTool {
        name: "process/scan_value",
        takes_handle: true,
        params: SCAN_VALUE_PARAMS,
        notes: &["aligned_default=true", "heap_only_default=ui_toggle_on"],
    },
    tool!("process/scan_next"),
    tool!("process/scan_string"),
    tool!("process/scan_pointer_to"),
    tool!("process/find_xrefs"),
    McpTool {
        name: "process/find_string_refs",
        takes_handle: true,
        params: FIND_STRING_REFS_PARAMS,
        notes: &[
            "heap_only_default=ui_toggle_on",
            "string_scan_pre_cap=1GiB",
            "code_hit_cap=4096",
            "response_includes_truncated",
        ],
    },
    tool!("process/generate_signature"),
    tool!("process/diff_memory"),
    tool!("process/find_function_bounds"),
    tool!("process/find_function_by_signature"),
    tool!("process/analyze_vtable"),
    tool!("process/read_rtti"),
    tool!("process/lookup_symbol"),
    tool!("process/find_function_by_name"),
    tool!("process/enum_handles"),
    tool!(no_handle "system/info"),
    tool!(no_handle "system/list_drivers"),
    tool!("process/get_command_line"),
    tool!("process/list_environment"),
    tool!(no_handle "script/get_context"),
    tool!(no_handle "script/validate"),
    tool!(no_handle "script/execute"),
];
pub fn all_tools() -> &'static [McpTool] {
    TOOLS
}
