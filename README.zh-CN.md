# buck-loop-lab

一个小型、诚实、可运行的 GitHub 作品集项目，主题是**Buck 变换器的数字闭环控制**：用纯 Python 实现平均状态空间被控对象 + 数字 PID 仿真，输出阶跃响应与 Bode 图的 CSV 和手写 SVG，并附一个明确标注的 STM32 骨架。

[English README](README.md)

## 它是什么

- **仅仿真**的教学/演示项目：RK4 积分的 Buck 平均模型、带抗积分饱和的离散 PID、带动态指标的闭环阶跃响应、解析开环 Bode 图。
- 仅使用标准库（`math`、`cmath`、`dataclasses`、`argparse`、`csv`、`pathlib`）。**不使用 numpy、scipy 或 matplotlib。**
- 离线、确定性、可测试。所有数据都是模型生成的合成数据。

## 它不是什么

- **不是硬件项目。** 这里没有开发板，没有烧录，也没有实测。
- **不是量产固件。** `firmware/` 是未经验证的模板：引脚、ADC 校准、PWM 配置均不保证正确。
- **不是真实测量数据。** 仓库中没有任何示波器或网络分析仪的实测结果，也不声称有。
- **不是 SPICE 级功率级模型。** 理想开关、仅 CCM、无损耗；详见 [docs/notes.md](docs/notes.md)。

## 安装与运行（离线）

```bash
python -m pip install -e "E:/doc_workbuddy/buck-loop-lab[dev]"
python -m buckloop all --out "E:/doc_workbuddy/buck-loop-lab/examples/output"
```

其他可实际运行的命令：

```bash
python -m buckloop bode
python -m buckloop step --setpoint 9 --duration 0.02
python -m buckloop step --help
```

`--out` 是**目录**，不存在时会自动创建；含空格的路径也能正常工作。

## 真实运行输出（摘自实际执行）

`python -m buckloop all --out "E:/doc_workbuddy/buck-loop-lab/examples/output"`：

```text
[all] output directory: E:\doc_workbuddy\buck-loop-lab\examples\output
[step] setpoint=9 V, dt=2e-06 s, samples=10001
  final value   : 9.0000 V
  rise (10-90%) : 0.000158 s
  overshoot     : 7.68 %
  settling (2%) : 0.004598 s
  steady error  : 0.0000 V
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\step_response.csv
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\step_response.svg

[bode] 60 points, 10 .. 100000 Hz
  resonance estimate : 1068.1 Hz
  peak magnitude     : 38.87 dB @ 1081.2 Hz
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\bode.csv
  wrote E:\doc_workbuddy\buck-loop-lab\examples\output\bode.svg
```

`python -m buckloop bode`：

```text
[bode] 60 points, 10 .. 100000 Hz
  resonance estimate : 1068.1 Hz
  peak magnitude     : 38.87 dB @ 1081.2 Hz
  wrote examples\output\bode.csv
  wrote examples\output\bode.svg
```

`python -m buckloop step --setpoint 9 --duration 0.02`：

```text
[step] setpoint=9 V, dt=2e-06 s, samples=10001
  final value   : 9.0000 V
  rise (10-90%) : 0.000158 s
  overshoot     : 7.68 %
  settling (2%) : 0.004598 s
  steady error  : 0.0000 V
  wrote examples\output\step_response.csv
  wrote examples\output\step_response.svg
```

输出文件：`step_response.csv`（`time_s,voltage_v,duty`）、`step_response.svg`（时间-电压曲线含给定线）、`bode.csv`（`freq_hz,magnitude_db,phase_deg`）、`bode.svg`（幅值/相位-对数频率）。SVG 为手写，均以 `<svg` 开头。

## 项目结构

```text
buck-loop-lab/
├── src/buckloop/
│   ├── __init__.py       公共 API 与版本号
│   ├── plant.py          Buck 平均模型、RK4、可选 ESR、占空比限幅
│   ├── controller.py     离散 PID、测量微分滤波、抗积分饱和
│   ├── sim.py            闭环阶跃响应与暂态指标
│   ├── frequency.py      解析控制-输出 Bode 与谐振频率估计
│   ├── svg.py            无依赖 SVG 写入器（两张图）
│   ├── cli.py            argparse 子命令：step / bode / all
│   └── __main__.py       python -m buckloop 入口
├── firmware/             STM32 模板，硬件上未验证
│   ├── README.md         诚实声明与适配说明
│   ├── loop.md           ADC -> PID -> PWM -> 定时节拍 伪代码
│   ├── pid.h             PID 状态与接口骨架
│   └── pid.c             镜像 Python 控制器算法
├── docs/notes.md         小信号推导与简化假设
├── tests/                pytest 测试
├── examples/output/      生成的 CSV + SVG（用 all 重新生成）
├── .github/workflows/ci.yml
├── pyproject.toml
└── LICENSE               MIT，2026 Gary7702
```

## 开发命令

```bash
python -m pytest tests --cov=buckloop --cov-report=term-missing
python -m coverage run -m pytest tests && python -m coverage report -m
python -m ruff check .
python -m ruff format --check .
python -m ruff format .
python -m build --no-isolation . --outdir dist
```

`pytest --cov` 需要 `pytest-cov`；若未安装，可改用上面的 `coverage run` 命令，它只依赖 `coverage` 包。

## 诚实声明

本作品集项目由 AI 辅助于 **2026 年 11 月** 构建，仅用于仿真演示。模型是理想化的合成模型；固件骨架**未在真实硬件上验证**；不声称任何量产用途、实测数据或硬件性能。将其用于真实变换器前，请自行适配并充分验证。
