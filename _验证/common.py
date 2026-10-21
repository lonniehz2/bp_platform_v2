# -*- coding: utf-8 -*-
"""
一键验证 · 公共模块
- 读取 config.json
- 统一的连接、彩色输出、步骤编排
"""
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, 'config.json')
STEPS_DIR = os.path.join(HERE, 'steps')

# ---------- 彩色输出（Windows 10+ 支持 ANSI）----------
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    _ANSI = True
except Exception:
    _ANSI = False


def _c(code, text):
    return ('\033[%sm%s\033[0m' % (code, text)) if _ANSI else text


def ok(t):    return _c('32', t)
def err(t):   return _c('31', t)
def warn(t):  return _c('33', t)
def info(t):  return _c('36', t)
def bold(t):  return _c('1', t)
def dim(t):   return _c('90', t)


def hr(ch='=', n=76):
    print(dim(ch * n))


def title(text):
    print()
    hr()
    print(bold('  ' + text))
    hr()


def load_config(path=None):
    p = path or CONFIG_PATH
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def build_env(cfg):
    """把 config 转成子进程环境变量"""
    db = cfg['db']
    env = os.environ.copy()
    env.update({
        'BP_DB_HOST': str(db['host']),
        'BP_DB_PORT': str(db['port']),
        'BP_DB_USER': str(db['user']),
        'BP_DB_PWD': str(db['password']),
        'BP_DB_NAME': str(db['database']),
        'BP_PROJ_DIR': cfg['paths']['project_dir'],
        'PYTHONIOENCODING': 'utf-8',
    })
    return env


def connect(cfg, database=None, timeout=10):
    """主进程直连（用于连通性检查与统计）"""
    import pymysql
    db = cfg['db']
    return pymysql.connect(
        host=db['host'], port=int(db['port']), user=db['user'], password=db['password'],
        database=database if database is not None else db['database'],
        charset='utf8mb4', connect_timeout=timeout, read_timeout=600)


# ---------- 步骤执行 ----------
class StepResult:
    def __init__(self, name, code, seconds, out):
        self.name = name
        self.code = code
        self.seconds = seconds
        self.out = out

    @property
    def passed(self):
        return self.code == 0


def run_step(script, cfg, extra_args=None, show=True, stream=True):
    """在子进程中执行 steps/<script>，注入环境变量"""
    path = os.path.join(STEPS_DIR, script)
    if not os.path.exists(path):
        print(err('  [缺失] 找不到步骤脚本: %s' % script))
        return StepResult(script, 127, 0.0, '')

    cmd = [sys.executable, path] + (extra_args or [])
    env = build_env(cfg)
    t0 = time.time()

    if stream:
        # 实时透传输出
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=env, text=True, encoding='utf-8', errors='replace')
        lines = []
        for line in proc.stdout:
            line = line.rstrip('\n')
            lines.append(line)
            if show:
                print('  ' + line)
        proc.wait()
        code = proc.returncode
        out = '\n'.join(lines)
    else:
        r = subprocess.run(cmd, capture_output=True, env=env, text=True,
                           encoding='utf-8', errors='replace')
        code = r.returncode
        out = (r.stdout or '') + (r.stderr or '')
        if show and out:
            for line in out.strip().split('\n'):
                print('  ' + line)

    dt = time.time() - t0
    return StepResult(script, code, dt, out)


def summary(results):
    title('验证汇总')
    print('  %-34s %-8s %s' % ('步骤', '结果', '耗时'))
    hr('-', 76)
    all_pass = True
    for r in results:
        flag = ok('PASS') if r.passed else err('FAIL')
        if not r.passed:
            all_pass = False
        print('  %-34s %-8s %.1fs' % (r.name, flag, r.seconds))
    hr('-', 76)
    if all_pass:
        print('  ' + ok(bold('全部通过')))
    else:
        print('  ' + err(bold('存在失败步骤，请查看上方日志')))
    print()
    return all_pass
