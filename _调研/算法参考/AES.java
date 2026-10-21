/**
 * Copyright (C), 杭州云门道科技有限公司
 * FileName:
 * Author:   hhd668@163.com
 * Date:     2019/3/7 16:12
 * Description:
 * History:
 * <author>          <time>          <version>          <desc>
 * 作者姓名           修改时间           版本号              描述
 */
package com.ymd.cloud.common.encrypt;

/**
 * 〈一句话功能简述〉<br> 
 *
 * @author hhd668@163.com
 * @create 2019/3/7
 * @since 1.0
 */
import java.io.UnsupportedEncodingException;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.KeySpec;
import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;
public class AES {
    private static final String VIPARA = "1269571869323221";//"1269571569321021";
    private static final String UTF_8 = "utf-8";
    //private static final int IV_SIZE = 16;
    private static final int KEY_SIZE = 16;//32;
    private static final String SALT = "4BDD60B281D31F1B70EC3AAA81F282BC";//"123896543abc3poda2d5";
    private static final String AES_PWD= "GM56771314";//加密密钥；

    /**
     *
     *
     * @param b
     * @return
     */
    private static String byte2HexStr(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < b.length; i++) {
            String s = Integer.toHexString(b[i] & 0xFF);
            if (s.length() == 1) {
                sb.append("0");
            }

            sb.append(s.toUpperCase());
        }

        return sb.toString();
    }

    private static SecretKey deriveKeySecurely(String password, int keySizeInBytes) {
        byte[] salt = SALT.getBytes();
        KeySpec keySpec = new PBEKeySpec(password.toCharArray(), salt,
                100 /* iterationCount */, keySizeInBytes * 8 /* key size in bits */);
        try {
            SecretKeyFactory keyFactory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA1");
            byte[] keyBytes = keyFactory.generateSecret(keySpec).getEncoded();
            return new SecretKeySpec(keyBytes, "AES");
        } catch (Exception e) {
            throw new RuntimeException("Deal with exceptions properly!", e);
        }
    }

    //加密
    public static byte[] aesEncrypt(String password,String content) {
        try {
            IvParameterSpec zeroIv = new IvParameterSpec(VIPARA.getBytes(UTF_8));
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            SecretKey key = deriveKeySecurely(password, KEY_SIZE);
            cipher.init(Cipher.ENCRYPT_MODE, key, zeroIv);
            byte[] encryptedData = cipher.doFinal(content.getBytes(UTF_8));
            int saltLength = 16;
            SecureRandom random = new SecureRandom();
            byte[] salt = new byte[saltLength];
            random.nextBytes(salt);
            return encryptedData;
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (NoSuchPaddingException e) {
            e.printStackTrace();
        } catch (UnsupportedEncodingException e) {
            e.printStackTrace();
        } catch (InvalidKeyException e) {
            e.printStackTrace();
        } catch (IllegalBlockSizeException e) {
            e.printStackTrace();
        } catch (BadPaddingException e) {
            e.printStackTrace();
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        }

        return null;
    }


    //解密
    public static String aesDecrypt(String password,String content) {
        try {
            byte[] byteMi = Base64Util.decode(content);
            IvParameterSpec zeroIv = new IvParameterSpec(VIPARA.getBytes(UTF_8));
            SecretKey key = deriveKeySecurely(password, KEY_SIZE);
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            cipher.init(Cipher.DECRYPT_MODE, key, zeroIv);
            byte[] decryptedData = cipher.doFinal(byteMi);
            return new String(decryptedData, "utf-8");
        }catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        } catch (NoSuchPaddingException e) {
            e.printStackTrace();
        } catch (InvalidKeyException e) {
            e.printStackTrace();
        } catch (IllegalBlockSizeException e) {
            e.printStackTrace();
        } catch (BadPaddingException e) {
            e.printStackTrace();
        } catch (UnsupportedEncodingException e) {
            e.printStackTrace();
        } catch (InvalidAlgorithmParameterException e) {

            e.printStackTrace();
        }
        return null;
    }

    //YMD 解密
    public static String aesYmdDecryptParam(String pwd,String para){
        return aesDecrypt(pwd,para);
    }
    //YMD 加密
    public static String aesYmdEncryptParam(String pwd,String para){
        return Base64Util.encode(aesEncrypt(pwd,para));
    }
    //YMD 16进制加密
    public static String aesYmdEncryptHexParam(String pwd,String para){
        return byte2HexStr(aesEncrypt(pwd,para));
    }

}
