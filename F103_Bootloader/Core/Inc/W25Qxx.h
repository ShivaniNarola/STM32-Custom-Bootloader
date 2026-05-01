/*
 * W25Qxx.h
 *
 *  Created on: 28-Apr-2026
 *      Author: Shivani
 */

#ifndef INC_W25QXX_H_
#define INC_W25QXX_H_

void W25Q_Reset (void);
uint32_t W25Q_ReadID (void);

void W25Q_Erase(uint32_t start_addr, uint32_t size);
void W25Q_Write(uint32_t addr, uint8_t *data, uint16_t len);
void W25Q_Read(uint32_t addr, uint8_t *buf, uint16_t len);
void W25Q_FastRead(uint32_t addr, uint8_t *data, uint16_t len);


#endif /* INC_W25QXX_H_ */
