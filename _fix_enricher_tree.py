# -*- coding: utf-8 -*-
"""补全器支持嵌套 children 递归 + 前端使用 spaceTypeLabel"""
import io
import re

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\web\DisplayEnricher.java')
s = io.open(P, encoding='utf-8').read()

if 'enrichChildren' not in s:
    # 在 enrich 里处理 children
    s = s.replace('''    public Map<String, Object> enrich(Object row) {''',
                  '''    /** 树形接口：最多递归 8 层，防止异常数据导致栈溢出 */
    private static final int MAX_TREE_DEPTH = 8;

    public Map<String, Object> enrich(Object row) {
        return enrich(row, 1);
    }

    private Map<String, Object> enrich(Object row, int depth) {''', 1)

    s = s.replace('''        if (row instanceof Map<?, ?> m) {
            @SuppressWarnings("unchecked")
            Map<String, Object> copy = new LinkedHashMap<>((Map<String, Object>) m);
            fill(copy);
            return copy;
        }
        Map<String, Object> map = objectMapper.convertValue(row, LinkedHashMap.class);
        fill(map);
        return map;''',
                  '''        Map<String, Object> map;
        if (row instanceof Map<?, ?> m) {
            @SuppressWarnings("unchecked")
            Map<String, Object> copy = new LinkedHashMap<>((Map<String, Object>) m);
            map = copy;
        } else {
            map = objectMapper.convertValue(row, LinkedHashMap.class);
        }
        fill(map);
        enrichChildren(map, depth);
        return map;''', 1)

    # 新增 enrichChildren
    s = s.replace('''    private void fill(Map<String, Object> map) {''',
                  '''    /**
     * 递归补全嵌套子节点。
     *
     * <p>组织树 / 空间树这类接口把层级放在 {@code children} 里，
     * 如果只补顶层，子节点仍会露出 UNIT、FLOOR 这类英文编码。</p>
     */
    private void enrichChildren(Map<String, Object> map, int depth) {
        if (depth >= MAX_TREE_DEPTH) {
            return;
        }
        for (Map.Entry<String, Object> e : map.entrySet()) {
            if (!(e.getValue() instanceof List<?> list) || list.isEmpty()) {
                continue;
            }
            List<Object> replaced = new java.util.ArrayList<>(list.size());
            boolean changed = false;
            for (Object item : list) {
                if (item instanceof Map<?, ?> || item != null
                        && !(item instanceof String) && !(item instanceof Number)) {
                    replaced.add(enrich(item, depth + 1));
                    changed = true;
                } else {
                    replaced.add(item);
                }
            }
            if (changed) {
                e.setValue(replaced);
            }
        }
    }

    private void fill(Map<String, Object> map) {''', 1)

    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ DisplayEnricher 支持 children 递归（深度 8）')
else:
    print('  - 已支持递归')

# 前端：空间类型优先用 label
SP = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'
t = io.open(SP, encoding='utf-8').read()
if 'spaceTypeLabel' not in t:
    t = t.replace('{{ data.spaceType }}', '{{ data.spaceTypeLabel || data.spaceType }}')
    t = t.replace('{{ current.spaceType }}', '{{ current.spaceTypeLabel || current.spaceType }}')
    io.open(SP, 'w', encoding='utf-8').write(t)
    print('  ✓ Spaces.vue 使用 spaceTypeLabel')
