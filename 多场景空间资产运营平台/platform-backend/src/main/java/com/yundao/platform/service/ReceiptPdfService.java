package com.yundao.platform.service;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.lowagie.text.Document;
import com.lowagie.text.Font;
import com.lowagie.text.Image;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfWriter;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Map;
import javax.imageio.ImageIO;
import org.springframework.stereotype.Service;

@Service
public class ReceiptPdfService {

    public byte[] render(Map<String, Object> receipt, Map<String, Object> config,
                         String verifyUrl, String verifyCode) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Document document = new Document(PageSize.A5, 42, 42, 42, 42);
            PdfWriter.getInstance(document, out);
            document.open();
            BaseFont bf = BaseFont.createFont("STSong-Light", "UniGB-UCS2-H", BaseFont.NOT_EMBEDDED);
            Font title = new Font(bf, 18, Font.BOLD);
            Font normal = new Font(bf, 11);
            Font small = new Font(bf, 9);

            document.add(new Paragraph(text(config, "title", "电子收据"), title));
            document.add(new Paragraph("ELECTRONIC RECEIPT", small));
            document.add(new Paragraph(" "));
            document.add(new Paragraph("收款单位 / Payee: " + text(config, "company", "-"), normal));
            document.add(new Paragraph("收据编号 / Receipt No: " + value(receipt, "receiptNo"), normal));
            document.add(new Paragraph("付款编号 / Payment No: " + value(receipt, "paymentNo"), normal));
            document.add(new Paragraph("付款金额 / Amount: CNY " + value(receipt, "amount"), normal));
            document.add(new Paragraph("付款方式 / Method: " + value(receipt, "paymentMethod"), normal));
            document.add(new Paragraph("开具时间 / Issued At: " + value(receipt, "issuedTime"), normal));
            document.add(new Paragraph("状态 / Status: " + value(receipt, "receiptStatus"), normal));
            document.add(new Paragraph(" "));
            document.add(new Paragraph("验真码 / Verify Code: " + verifyCode, small));
            document.add(new Paragraph(text(config, "footer", "本收据为收款凭证，非发票。"), small));
            document.add(new Paragraph("This is a payment receipt, not an invoice.", small));
            Image qr = Image.getInstance(qrPng(verifyUrl, 180));
            qr.setAlignment(Image.ALIGN_CENTER);
            document.add(qr);
            document.add(new Paragraph("扫码验真 / Scan to verify", small));
            document.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new IllegalStateException("收据 PDF 生成失败", e);
        }
    }

    public String verifyCode(Map<String, Object> receipt) {
        try {
            String raw = value(receipt, "receiptNo") + value(receipt, "paymentNo");
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(raw.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 4; i++) sb.append(String.format("%02X", digest[i]));
            return sb.toString();
        } catch (Exception e) {
            return "-";
        }
    }

    public String sha256(byte[] bytes) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    private byte[] qrPng(String text, int size) throws Exception {
        BitMatrix matrix = new QRCodeWriter().encode(text, BarcodeFormat.QR_CODE, size, size);
        BufferedImage image = new BufferedImage(size, size, BufferedImage.TYPE_INT_RGB);
        for (int x = 0; x < size; x++) for (int y = 0; y < size; y++) {
            image.setRGB(x, y, matrix.get(x, y) ? 0x000000 : 0xFFFFFF);
        }
        ByteArrayOutputStream png = new ByteArrayOutputStream();
        ImageIO.write(image, "png", png);
        return png.toByteArray();
    }

    private String text(Map<String, Object> config, String key, String fallback) {
        Object v = config == null ? null : config.get(key);
        return v == null || String.valueOf(v).isBlank() ? fallback : String.valueOf(v);
    }

    private String value(Map<String, Object> receipt, String key) {
        Object v = receipt.get(key);
        return v == null ? "-" : String.valueOf(v);
    }
}
