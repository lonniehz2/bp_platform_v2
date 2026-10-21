package com.yundao.bp.grant.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.entity.GrantTask;
import com.yundao.bp.grant.mapper.GrantTaskMapper;
import com.yundao.bp.grant.mq.GrantDispatchProducer;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 授权任务兜底重试。
 *
 * <p>解决两类问题：
 * <ol>
 *   <li><b>MQ 投递失败</b>：apply 时 MQ 不可用 → 任务停在 PENDING，这里补投</li>
 *   <li><b>消费者处理丢失</b>：消息被吞 → 任务超时仍在 PENDING，这里补投</li>
 * </ol>
 *
 * <p>只捞 60 秒前创建、且重试次数未超限的 PENDING 任务，避免与正常流程抢跑。
 */
@Component
public class GrantRetryJob {

    private static final Logger log = LoggerFactory.getLogger(GrantRetryJob.class);
    private static final int MAX_RETRY = 3;

    private final GrantTaskMapper taskMapper;
    private final GrantDispatchProducer producer;

    public GrantRetryJob(GrantTaskMapper taskMapper, GrantDispatchProducer producer) {
        this.taskMapper = taskMapper;
        this.producer = producer;
    }

    @Scheduled(fixedDelay = 60_000, initialDelay = 30_000)
    public void retryPending() {
        LocalDateTime before = LocalDateTime.now().minusSeconds(60);
        List<GrantTask> list = taskMapper.selectList(new LambdaQueryWrapper<GrantTask>()
                .eq(GrantTask::getTaskStatus, GrantTaskStatus.PENDING.name())
                .lt(GrantTask::getCreateTime, before)
                .and(w -> w.isNull(GrantTask::getRetryCount)
                        .or().lt(GrantTask::getRetryCount, MAX_RETRY))
                .last("LIMIT 50"));
        if (list.isEmpty()) {
            return;
        }
        log.info("补投 PENDING 授权任务 {} 个", list.size());
        for (GrantTask t : list) {
            producer.publishDispatch(t.getId());
        }
    }
}
