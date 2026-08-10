# Miniconda installer / Miniconda 安装包

The GitHub release package includes the following official Miniconda installer so first-time setup does not depend on downloading it separately. The source repository intentionally does not track this large binary; `setup_runtime.ps1` downloads and verifies the same file when needed.

GitHub 的一键包会附带以下官方 Miniconda 安装程序，因此首次安装无需另外下载 Miniconda。源码仓库不保存这个大体积二进制文件；缺少时，`setup_runtime.ps1` 会从官方下载并校验同一文件。

- File: `Miniconda3-py312_26.5.3-2-Windows-x86_64.exe`
- Official source: <https://repo.anaconda.com/miniconda/Miniconda3-py312_26.5.3-2-Windows-x86_64.exe>
- SHA-256: `75E829B26BD7B33B1DCE118639B8F39E561A6EBAA3B593B633D7445DD1A2D65A`
- Included license copy: [`MINICONDA_EULA.txt`](MINICONDA_EULA.txt)
- Current Miniconda terms: <https://www.anaconda.com/legal/terms/miniconda>

Miniconda is provided by Anaconda, Inc. and is not part of this project's GPL-3.0 source license. Inclusion does not imply endorsement. The application creates its environment from `conda-forge` and does not add Miniconda to `PATH` or register it as the system Python.

Miniconda 由 Anaconda, Inc. 提供，不属于本项目 GPL-3.0 源码许可范围。随包分发不代表官方背书。工具通过 `conda-forge` 创建环境，不会把 Miniconda 加入 `PATH`，也不会将其注册为系统 Python。
