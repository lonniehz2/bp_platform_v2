package com.yundao.platform.common.id;

import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Component;

@Component
public class IdGenerator {

    private final AtomicLong sequence = new AtomicLong(System.currentTimeMillis() * 1000L);

    public long nextId() {
        return sequence.incrementAndGet();
    }
}
