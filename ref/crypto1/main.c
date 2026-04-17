#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "crapto1.h"

/**
 * @brief Crypto1 16 组确定性加解密测试程序
 */
int main() {
    // 预定义 16 个不同的 48-bit Key
    uint64_t test_keys[16] = {
        0xFFFFFFFFFFFFULL, 0x000000000000ULL, 0xA0A1A2A3A4A5ULL, 0xB0B1B2B3B4B5ULL,
        0x4B4559203132ULL, 0xD3F7D3F7D3F7ULL, 0x123456789ABCULL, 0xABCDEF123456ULL,
        0xDEADBEEFCAFEULL, 0xFEEDFACECAFEULL, 0x112233445566ULL, 0x888888888888ULL,
        0x555555555555ULL, 0x665544332211ULL, 0x010203040506ULL, 0x1337C08D1337ULL
    };

    // 预定义 16 个不同的 32-bit 明文输入
    uint32_t test_inputs[16] = {
        0x12345678, 0x87654321, 0x00000000, 0xFFFFFFFF,
        0x55AA55AA, 0xAA55AA55, 0x1337BEEF, 0xDEADBABE,
        0xC0FFEE01, 0x01020304, 0x99887766, 0x5A5A5A5A,
        0xA5A5A5A5, 0x0F0F0F0F, 0xF0F0F0F0, 0x11223344
    };

    printf("Crypto1 确定性加解密测试 (16组数据)\n");
    printf("===============================================================================\n");
    printf("%-2s | %-12s | %-8s | %-8s | %-8s | %-4s\n", "ID", "Key (48-bit)", "Plain", "Cipher", "Decrypted", "Stat");
    printf("-------------------------------------------------------------------------------\n");

    for (int i = 0; i < 16; i++) {
        uint64_t key = test_keys[i];
        uint32_t plain = test_inputs[i];

        // 1. 加密
        struct Crypto1State *s_enc = crypto1_create(key);
        if (!s_enc) continue;
        // crypto1_word 返回流密钥，加密需手动 XOR
        uint32_t ks_enc = crypto1_word(s_enc, plain, 1);
        uint32_t cipher = plain ^ ks_enc;
        crypto1_destroy(s_enc);

        // 2. 解密
        struct Crypto1State *s_dec = crypto1_create(key);
        if (!s_dec) continue;
        // 解密时输入密文，反馈后返回相同流密钥
        uint32_t ks_dec = crypto1_word(s_dec, cipher, 1);
        uint32_t decrypted = cipher ^ ks_dec;
        crypto1_destroy(s_dec);

        printf("%02d | %012llX | %08X | %08X | %08X  | %s\n", 
               i + 1, key, plain, cipher, decrypted, 
               (plain == decrypted) ? "OK" : "FAIL");
    }

    printf("===============================================================================\n");
    printf("测试完成。\n");

    return 0;
}
