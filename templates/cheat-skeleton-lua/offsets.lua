-- offsets.lua — signatures and resolution helpers

-- Placeholder signatures. Replace after dumping with IDA/ReClass.
SIG_ENTITY_LIST  = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ??"  -- UNVERIFIED
SIG_LOCAL_PLAYER = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ??"  -- UNVERIFIED
SIG_VIEW_MATRIX  = "48 8D 05 ?? ?? ?? ?? 48 89 ?? 48 ?? ??" -- UNVERIFIED

-- Resolve RIP-relative mov/lea instruction: hit + displacement + instruction length.
function resolve_rip(hit, disp_off, insn_len)
    if hit == 0 then return 0 end
    local disp = g_proc:r32(hit + disp_off)
    return hit + insn_len + disp
end

-- Resolve all signatures. Return false if any signature is stale.
function resolve_all()
    if not g_proc or not g_proc:alive() or g_base == 0 or g_size == 0 then return false end

    local hit_el = g_proc:find_code_pattern(g_base, g_size, SIG_ENTITY_LIST)
    if hit_el == 0 then log("[offsets] entity_list sig stale"); return false end
    g_entity_list = resolve_rip(hit_el, 3, 7)

    local hit_lp = g_proc:find_code_pattern(g_base, g_size, SIG_LOCAL_PLAYER)
    if hit_lp == 0 then log("[offsets] local_player sig stale"); return false end
    g_local_player = resolve_rip(hit_lp, 3, 7)

    local hit_vm = g_proc:find_code_pattern(g_base, g_size, SIG_VIEW_MATRIX)
    if hit_vm == 0 then log("[offsets] view_matrix sig stale"); return false end
    g_view_matrix = resolve_rip(hit_vm, 3, 7)

    return g_entity_list ~= 0 and g_local_player ~= 0 and g_view_matrix ~= 0
end
