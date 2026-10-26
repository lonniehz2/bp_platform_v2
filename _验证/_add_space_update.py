# -*- coding: utf-8 -*-
"""后端：空间节点支持更新（PUT /spaces/{id}）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# ---------- 1) Service 接口 ----------
P = os.path.join(SRC, 'service', 'SpaceService.java')
s = io.open(P, encoding='utf-8').read()
if 'SpaceVO update(' not in s:
    s = s.replace('    SpaceVO get(Long id);',
                  '''    SpaceVO get(Long id);

    /** 更新空间节点（名称/编码/面积/排序/状态/备注）。 */
    SpaceVO update(Long id, com.yundao.bp.asset.dto.SpaceUpdateCmd cmd);''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('SpaceService 已加 update')

# ---------- 2) Service 实现 ----------
P = os.path.join(SRC, 'service', 'impl', 'SpaceServiceImpl.java')
s = io.open(P, encoding='utf-8').read()
if 'public SpaceVO update(' not in s:
    impl = '''
    @Override
    public SpaceVO update(Long id, com.yundao.bp.asset.dto.SpaceUpdateCmd cmd) {
        AssetSpace space = spaceMapper.selectById(id);
        if (space == null) {
            throw BizException.notFound("空间节点");
        }
        // 编码唯一（排除自身）
        Long dup = spaceMapper.selectCount(new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getSpaceCode, cmd.spaceCode())
                .ne(AssetSpace::getId, id));
        if (dup != null && dup > 0) {
            throw BizException.duplicated("空间编码已存在: " + cmd.spaceCode());
        }
        space.setSpaceName(cmd.spaceName());
        space.setSpaceCode(cmd.spaceCode());
        if (cmd.area() != null) {
            space.setArea(cmd.area());
        }
        if (cmd.sortNo() != null) {
            space.setSortNo(cmd.sortNo());
        }
        if (cmd.status() != null && !cmd.status().isBlank()) {
            space.setStatus(cmd.status());
        }
        space.setRemark(cmd.remark());
        // fullName 由父级全名 + 本节点名称组成，改名后同步
        String parentFull = null;
        if (space.getParentId() != null) {
            AssetSpace parent = spaceMapper.selectById(space.getParentId());
            if (parent != null) {
                parentFull = parent.getFullName();
            }
        }
        space.setFullName((parentFull == null || parentFull.isBlank() ? "" : parentFull)
                + cmd.spaceName());
        spaceMapper.updateById(space);
        return get(id);
    }

    // ---------- 内部 ----------
'''
    s = s.replace('    // ---------- 内部 ----------', impl, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('SpaceServiceImpl 已加 update')

# ---------- 3) Controller ----------
P = os.path.join(SRC, 'controller', 'SpaceController.java')
s = io.open(P, encoding='utf-8').read()
if 'PutMapping' not in s:
    s = s.replace('''    @com.yundao.bp.iam.security.RequirePerm("asset:space:view")
    @GetMapping("/{id}")''',
'''    /** 更新空间节点信息（不动层级关系）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:space:create")
    @org.springframework.web.bind.annotation.PutMapping("/{id}")
    public R<SpaceVO> update(@PathVariable Long id,
                             @Valid @RequestBody com.yundao.bp.asset.dto.SpaceUpdateCmd cmd) {
        return R.ok(spaceService.update(id, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:space:view")
    @GetMapping("/{id}")''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('SpaceController 已加 PUT /{id}')
