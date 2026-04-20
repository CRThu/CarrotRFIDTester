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
    *   实现完整的 Mifare Classic 指令集（`read_block`, `write_block`, `increment` 等），并自动处理 PN532 的 `InDataExchange` 指令封装。
    *   **认证逻辑**: `authenticate` 方法支持硬件认证（PN532 内置）与软件认证切换。
    *   **协议安全**: 在卡片层实现了 Mifare Classic 的三轮认证（3-pass authentication）计算逻辑，调用加密层的原子函数（如位移、滤波）完成安全交互，保持加密算法层的抽象性。

### 第四层：加密算法层 (Crypto Layer)
*   **目录**: `src/crft/crypto/`
*   **职责**: 提供卡片交互所需的底层加密/解密原子操作。
*   **核心模块**: `AES`, `DES`, `MifareCrypto1` (Crypto1 算法的位级实现)。
*   **设计原则**: 仅暴露标准的加密/解密接口及算法原子组件，不包含具体的业务协议逻辑（如三轮认证流程）。

## 3. 开发与测试指南

*   **环境管理**: 使用 `uv`。
*   **运行脚本**: 必须使用 `uv run <script_path>`。
*   **自动化测试**: 必须使用 `pytest` 执行。
*   **配置**: 硬件参数（如 COM 端口）应通过环境变量 `CRFT_PORT` 或配置文件读取，严禁硬编码在核心库中。
*   **代码规范**: 
    *   方法和类必须有 Docstring。
    *   注释应简洁明了。
    *   异常处理必须覆盖超时和通信错误。

## 4. 依赖项
*   `pyserial`: 串口通信。
*   `loguru`: 结构化日志记录。
*   `pytest`: 测试框架。
