package com.yundao.bp.dev.iot;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟拉取：返回空列表，页面/任务可跑通流程。 */
@Component
@ConditionalOnProperty(name = "bp.dev.meter-mode", havingValue = "mock", matchIfMissing = true)
public class MockMeterPullClient implements MeterPullClient {

    @Override
    public List<Reading> pull(List<String> meterNos, LocalDate from, LocalDate to) {
        return new ArrayList<>();
    }
}
