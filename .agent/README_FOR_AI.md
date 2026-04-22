# CarrotRFIDTester 架构说明书 (AI 专用)

## 1. 项目概述
`CarrotRFIDTester` 是一个用于测试 RFID 卡片和 PN532 读卡器的自动化测试框架。项目采用分层架构，旨在实现硬件通信、芯片驱动、卡片逻辑与加密算法的解耦。

## 2. 四层架构体系

### 第一层：硬件传输层 (Hardware/Transport Layer)
*   **目录**: `src/crft/hardware/`
*   **职责**: 负责底层的字节流传输。
*   **核心类**: `SerialTransport` (处理 RS232/HSU 串口通信)。
*   **设计原则**: 定义统一的 `BaseTransport` 接口，以便后续扩展 TCP/IP 或 USB 传输。

### 第二层：驱动层 (Driver Layer)
*   **目录**: `src/crft/drivers/`
*   **职责**: 实现特定芯片的协议封装（如 PN532 的 NXP 标准帧格式）。
*   **核心类**: `PN532_HSU`。
*   **逻辑**: 包含 ACK 处理、唤醒序列（Wakeup）、以及读取/写入数据帧。

### 第三层：卡片逻辑层 (Card Layer)
*   **目录**: `src/crft/cards/`
*   **职责**: 实现各种 RFID 卡片协议逻辑（如 ISO14443A, Mifare Classic）。
*   **核心类**: `BaseCard`, `MifareClassicCard`。
*   **逻辑**: 
    *   处理寻卡、防碰撞、选择卡片等 ISO14443A 基础流程。
    *   实现完整的 Mifare Classic 指令集（`read_block`, `write_block`, `increment` 等），通过调用读卡器层的 `transceive` 进行交互，实现卡片逻辑与读卡器硬件指令（如 `InDataExchange`）的解耦。
    *   **认证逻辑**: `authenticate` 方法使用 PN532 内置的硬件认证功能。
    *   **协议安全**: 目前依赖硬件层处理 Mifare Classic 的三轮认证，加密算法层主要提供离线的算法验证支持。

### 第四层：加密算法层 (Crypto Layer)
*   **目录**: `src/crft/crypto/`
*   **职责**: 提供卡片交互所需的底层加密/解密原子操作。
*   **核心模块**: 
    *   `AES128Crypto`: 实现 AES-128 CBC 模式。
    *   `MifareCrypto1`: 有状态的流加密引擎，支持 Mifare Classic 认证。
*   **设计原则**: 
    *   **接口统一**: 继承 `BaseCrypto` 基类，确保 `encrypt` 和 `decrypt` 接口一致性。
    *   **状态隔离**: 对于 `MifareCrypto1` 等流加密，通过 `initialize` 严格管理内部 LFSR 状态；对于 `AES128Crypto` 等分组加密，则保持无状态设计。
*   **算法归口**: 包含算法特有的逻辑（如 Mifare 的 `prng_successor` 或 AES 的填充校验），确保算法实现的纯粹性，不包含卡片协议层逻辑。


### 第五层：工具层 (Tools Layer)
*   **目录**: `src/crft/tools/`
*   **职责**: 提供命令行接口 (CLI) 以直接调用核心加密/通信逻辑。
*   **运行方式**: `uv run aes128-cli -m encrypt -i <hex> -k <key>`


## 3. 开发与测试指南

*   **环境管理**: 使用 `uv`。
*   **运行脚本**: 必须使用 `uv run <script_path>`。
*   **自动化测试**:
    *   使用 `pytest` 执行测试。
    *   测试结构与源码模块对齐：
        *   `tests/crypto/`: 算法层测试。
        *   `tests/cards/`: 卡片协议层测试。
        *   `tests/drivers/`: 硬件驱动层测试。
    *   执行特定模块测试: `uv run pytest tests/crypto/`
*   **配置**: 硬件参数（如 COM 端口）应通过环境变量 `CRFT_PORT` 或配置文件读取，严禁硬编码在核心库中。
*   **代码规范**: 
    *   方法和类必须有 Docstring。
    *   注释应简洁明了。
    *   异常处理必须覆盖超时和通信错误。

## 4. 依赖项
*   `pyserial`: 串口通信。
*   `loguru`: 结构化日志记录。
*   `pytest`: 测试框架。
