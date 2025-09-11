#!/usr/bin/env python3
"""Test runner for pa1.

功能:
1. 读取 tests/in 与 tests/out 下的编号文件 (形如 1.txt, 2.txt ...)。
2. 对每个输入以标准输入运行已编译可执行文件 ./pa1 (位于工作区根目录)。
3. 捕获标准输出, 将第一次出现 "EOS" 之前的内容记为 Output[n]，其后内容记为 Extra[n]。
4. 实时更新进度条: [====>.....] x% Running test n (单行刷新)。
5. 比较 Output[n] 与 tests/out/n.txt 不同之处，输出差异 (逐行 diff)。统计 Success / Fail。
6. 全部结束打印汇总: Finished, Success X, Fail Y。
7. 询问是否查看额外信息 (Extra 部分)，若 y 则逐个打印。

假设: tests/out 目录存在且文件名与 tests/in 对应。如果缺失则计为失败。
"""

from __future__ import annotations
import os
import re
import sys
import subprocess
from typing import List, Dict, Tuple

ROOT = os.path.abspath(os.path.dirname(__file__))
IN_DIR = os.path.join(ROOT, 'tests', 'in')
OUT_DIR = os.path.join(ROOT, 'tests', 'out')
EXEC = os.path.join(ROOT, 'pa1')  # 假设可执行名为 pa1
CLANG = '/opt/homebrew/Cellar/llvm/20.1.5/bin/clang++'
CLANG_ARGS = [
    '-g','-O0','-fno-inline','-std=c++11','-fsanitize=address,leak,undefined',
    '-Wall','-Wextra','-Wpedantic','-Werror=vla','-std=c++11','--target=aarch64-apple-darwin'
]

BAR_WIDTH = 25  # 进度条宽度 (含左右括号外的 '=' 区域长度)

def numeric_key(name: str) -> int:
    try:
        return int(re.sub(r'\D', '', name))
    except ValueError:
        return 10**9

def load_test_files() -> List[Tuple[int, str, str]]:
    if not os.path.isdir(IN_DIR):
        print(f'输入目录不存在: {IN_DIR}', file=sys.stderr)
        sys.exit(1)
    in_files = [f for f in os.listdir(IN_DIR) if f.endswith('.txt')]
    in_files.sort(key=numeric_key)
    tests: List[Tuple[int, str, str]] = []
    for f in in_files:
        num_match = re.match(r'(\d+)\.txt$', f)
        if not num_match:
            continue
        n = int(num_match.group(1))
        in_path = os.path.join(IN_DIR, f)
        out_path = os.path.join(OUT_DIR, f)  # 期望输出同名
        tests.append((n, in_path, out_path))
    return tests

def build_executable() -> None:
    print('Compiling:')
    cpp_files = [os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith('.cpp')]
    if not cpp_files:
        print('未找到任何 .cpp 文件用于编译', file=sys.stderr)
        sys.exit(1)
    cmd = [CLANG] + CLANG_ARGS + ['-o', EXEC] + cpp_files
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print('  Build success.')
    except subprocess.CalledProcessError as e:
        print('编译失败:')
        print(e.stdout.decode('utf-8', errors='replace'))
        sys.exit(1)

def run_single_test(in_file: str) -> str:
    env = os.environ.copy()
    # 为 AddressSanitizer / LeakSanitizer 配置环境变量
    # 若已有外部设置则不覆盖关键选项，采用更新合并方式。
    default_asan = 'detect_leaks=1:color=always:abort_on_error=0:report_objects=0'
    user_asan = env.get('ASAN_OPTIONS')
    if user_asan:
        # 合并不重复的键值
        existing_keys = {kv.split('=')[0] for kv in user_asan.split(':') if '=' in kv}
        merged = list(user_asan.split(':'))
        for kv in default_asan.split(':'):
            k = kv.split('=')[0] if '=' in kv else kv
            if k not in existing_keys:
                merged.append(kv)
        env['ASAN_OPTIONS'] = ':'.join(merged)
    else:
        env['ASAN_OPTIONS'] = default_asan
    # Leak sanitizer 抑制文件（若存在 lsan.supp）
    supp_path = os.path.join(ROOT, 'lsan.supp')
    if os.path.isfile(supp_path):
        env.setdefault('LSAN_OPTIONS', f'suppressions={supp_path}')
    try:
        with open(in_file, 'rb') as fin:
            proc = subprocess.run(
                [EXEC],
                stdin=fin,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                check=False,
                env=env,
            )
    except FileNotFoundError:
        print(f'未找到可执行文件 {EXEC}. 请先编译.', file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        return 'TIMEOUT\n'
    return proc.stdout.decode('utf-8', errors='replace')

def split_output(raw: str) -> Tuple[str, str]:
    """根据第一次出现包含"> 0"的菜单起始 (下一轮循环) 分段，最终再依据 EOS 切分。

    逻辑:
    - 程序每轮循环都会打印菜单, 以空行+Welcome开头, 最后一行是 "> " 或 ">"。
    - 输入序列里包含 0 结束; 最后一次循环后的输出含 EOS。
    - 用户需求: 以 EOS 前作为 Output，其后 Extra。若无 EOS 则全部归 Output。
    此函数单纯做 EOS 切分 (需求指定), 但允许保留末尾 prompt 的额外空格。
    """
    if 'EOS' in raw:
        pre, post = raw.split('EOS', 1)
        return pre, post
    return raw, ''

def format_progress(current: int, total: int) -> str:
    pct = current / total
    filled = int(pct * BAR_WIDTH)
    filled = min(filled, BAR_WIDTH)
    bar = '[' + '=' * (filled - 1) + ('>' if filled > 0 and filled < BAR_WIDTH else ('=' if filled == BAR_WIDTH else '')) + ' ' * (BAR_WIDTH - filled) + ']'
    percent_disp = f'{int(pct * 100):3d}%'
    return f'\r{bar} {percent_disp} Running test {current}'

RESET = '\x1b[0m'
RED = '\x1b[31m'
GREEN = '\x1b[32m'
CYAN = '\x1b[36m'
YELLOW = '\x1b[33m'

def diff_lines(expected: str, actual: str) -> List[str]:
    """Git 风格彩色 diff；忽略行尾空白差异。"""
    exp_lines = expected.splitlines()
    act_lines = actual.splitlines()
    max_len = max(len(exp_lines), len(act_lines))
    diffs: List[str] = []
    for i in range(max_len):
        e_raw = exp_lines[i] if i < len(exp_lines) else ''
        a_raw = act_lines[i] if i < len(act_lines) else ''
        # 忽略尾部空白
        if e_raw.rstrip() == a_raw.rstrip():
            continue
        line_no = f'{i+1:>4d}'
        diffs.append(f'{YELLOW}Line {line_no}{RESET}')
        diffs.append(f'{RED}- {e_raw}{RESET}')
        diffs.append(f'{GREEN}+ {a_raw}{RESET}')
    return diffs

def main():
    build_executable()
    tests = load_test_files()
    if not tests:
        print('未发现测试输入文件 (tests/in/*.txt)')
        return
    total = len(tests)
    print('Running:')

    outputs: Dict[int, str] = {}
    extras: Dict[int, str] = {}
    fail = 0
    success = 0
    failure_reports: List[str] = []

    for idx, (n, in_path, out_path) in enumerate(tests, 1):
        print(format_progress(idx, total), end='', flush=True)
        raw = run_single_test(in_path)
        pre, post = split_output(raw)
        outputs[n] = pre
        extras[n] = post

        if not os.path.isfile(out_path):
            fail += 1
            failure_reports.append(f'Test {n}: missing expected file {out_path}')
            continue
        with open(out_path, 'r', encoding='utf-8', errors='replace') as f:
            expected = f.read()
        diffs = diff_lines(expected, pre)
        if diffs:
            fail += 1
            failure_reports.append(f'Test {n}:\n' + '\n'.join(diffs))
        else:
            success += 1
    # 结束进度条行
    print('\r' + ' ' * 80 + '\r', end='')

    for rep in failure_reports:
        print(rep)
    summary_color = GREEN if fail == 0 else (YELLOW if success > 0 else RED)
    print(f'{summary_color}Finished, Success {success}, Fail {fail}{RESET}')

    try:
        choice = input('Would u like to see extra info (y/n): ').strip().lower()
    except EOFError:
        return
    if choice == 'y':
        for n in sorted(extras):
            print(f'Test {n}:')
            extra = extras[n]
            if extra.strip():
                print(extra.rstrip('\n'))
            else:
                print('<NO EXTRA OUTPUT>')

if __name__ == '__main__':
    main()
