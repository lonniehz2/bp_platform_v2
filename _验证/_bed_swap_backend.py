# -*- coding: utf-8 -*-
"""宿舍床位调换：把一个生效合同的床位置换到同组织另一张空床。

接口：POST /contracts/{id}/swap-bed  {targetHouseId, reason}
规则：
  · 原合同必须生效中，且当前房源为宿舍床位（DORMITORY / BED_MONTH）
  · 目标房源必须是同组织、宿舍床位、当前无生效合同
  · 置换后释放旧床、占用新床，合同房源字段更新，租金不变
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')

# ---------- Service 接口 ----------
S = os.path.join(J, 'service', 'ContractService.java')
s = io.open(S, encoding='utf-8').read()
if 'swapBed' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 床位调换：把生效合同迁移到目标床位（宿舍场景）。 */
    ContractVO swapBed(Long id, Long targetHouseId, String reason);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('ContractService：swapBed 已加')

# ---------- 实现 ----------
I = os.path.join(J, 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'swapBed' not in s:
    inject = '''
    /** 房源（床位调换时校验与更新状态） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper bedHouseMapper;
'''
    if 'bedHouseMapper' not in s:
        j = s.find('    public ContractServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    impl = '''
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public ContractVO swapBed(Long id, Long targetHouseId, String reason) {
        BizContract e = require(id);
        if (!ContractStatus.EFFECTIVE.name().equals(e.getContractStatus())
                && !ContractStatus.RENEWING.name().equals(e.getContractStatus())) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "只有生效中的合同可以调换床位");
        }
        if (targetHouseId == null || targetHouseId.equals(e.getHouseId())) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("目标床位不能与原床位相同");
        }
        if (bedHouseMapper == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("床位服务未就绪");
        }
        com.yundao.bp.asset.entity.AssetHouse from =
                bedHouseMapper.selectById(e.getHouseId());
        com.yundao.bp.asset.entity.AssetHouse to = bedHouseMapper.selectById(targetHouseId);
        if (from == null || to == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("房源");
        }
        if (!"DORMITORY".equals(from.getHouseType()) || !"DORMITORY".equals(to.getHouseType())) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid(
                    "床位调换仅适用于宿舍房源");
        }
        if (to.getOrgId() != null && from.getOrgId() != null
                && !to.getOrgId().equals(from.getOrgId())) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("不能跨组织调换床位");
        }
        Long occupied = mapper.selectCount(new LambdaQueryWrapper<BizContract>()
                .eq(BizContract::getHouseId, targetHouseId)
                .in(BizContract::getContractStatus,
                        List.of(ContractStatus.EFFECTIVE.name(),
                                ContractStatus.RENEWING.name())));
        if (occupied != null && occupied > 0) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "目标床位已被占用，不能调换");
        }

        // 释放旧床 → 占用新床（占用流水由 OccupancyService 统一维护）
        occupancyService.releaseByContract(e.getId(), java.time.LocalDate.now());
        occupancyService.occupyByContract(e.getId(), to.getId(), to.getSpaceId(),
                e.getLesseePersonId(), e.getLeaseStart(), e.getLeaseEnd());

        e.setHouseId(to.getId());
        e.setSpaceId(to.getSpaceId());
        String note = (reason == null || reason.isBlank()) ? "床位调换" : reason;
        e.setRemark(appendNote(e.getRemark(),
                "[" + java.time.LocalDate.now() + "] 床位由 " + from.getHouseCode()
                        + " 调换至 " + to.getHouseCode() + "：" + note));
        e.setUpdateTime(java.time.LocalDateTime.now());
        mapper.updateById(e);
        log.info("合同 {} 床位调换：{} → {}", e.getContractNo(),
                from.getHouseCode(), to.getHouseCode());
        return ContractVO.from(e);
    }

    /** 追加备注，保留历史。 */
    private String appendNote(String old, String add) {
        if (old == null || old.isBlank()) {
            return add;
        }
        return old + "；" + add;
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('ContractServiceImpl：swapBed 已实现')

# ---------- Controller ----------
C = os.path.join(J, 'controller', 'ContractController.java')
s = io.open(C, encoding='utf-8').read()
if 'swap-bed' not in s:
    block = '''
    /** 宿舍床位调换。 */
    @PostMapping("/{id}/swap-bed")
    @com.yundao.bp.iam.security.RequirePerm("biz:contract:update")
    public R<ContractVO> swapBed(@PathVariable Long id, @RequestBody SwapBedCmd cmd) {
        return R.ok(contractService.swapBed(id, cmd.targetHouseId(), cmd.reason()));
    }

    public record SwapBedCmd(Long targetHouseId, String reason) {
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('ContractController：/swap-bed 已加')

print('完成')
