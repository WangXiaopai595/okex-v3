/*
 Navicat Premium Data Transfer

 Source Server         : my
 Source Server Type    : MariaDB
 Source Server Version : 100509
 Source Host           : 1.15.233.247:3306
 Source Schema         : exchange

 Target Server Type    : MariaDB
 Target Server Version : 100509
 File Encoding         : 65001

 Date: 01/07/2021 15:14:10
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for exchange_record
-- ----------------------------
DROP TABLE IF EXISTS `exchange_record`;
CREATE TABLE `exchange_record`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `btc_balance` decimal(15, 8) NOT NULL COMMENT 'btc余额',
  `usdt_balance` decimal(15, 6) NOT NULL COMMENT 'usdt余额',
  `exchange_usdt` decimal(15, 6) NOT NULL COMMENT '本次交易usdt数量',
  `exchange_btc` decimal(15, 8) NOT NULL COMMENT '本次交易btc数量',
  `exchange_mod` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_croatian_ci NOT NULL COMMENT '交易类型 sell  buy',
  `exchange_rate` float(7, 4) NOT NULL COMMENT '交易比例',
  `btc_price` decimal(15, 6) NOT NULL COMMENT 'btc当前价格',
  `total_balance` decimal(15, 6) NOT NULL COMMENT '当前账户总价值',
  `created_time` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 32 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_croatian_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
