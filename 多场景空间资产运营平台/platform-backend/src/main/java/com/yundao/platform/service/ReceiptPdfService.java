package com.yundao.platform.service;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.lowagie.text.Document;
import com.lowagie.text.Font;
import com.lowagie.text.Image;
import com.lowagie.text.PageSize;
import com.lowagie.text.Rectangle;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfWriter;
import com.lowagie.text.pdf.PdfContentByte;
import java.util.Base64;
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
        if (config != null && config.get("canvas") instanceof Map<?, ?> canvas) {
            return renderCanvas(receipt, canvas, config, verifyUrl, verifyCode);
        }
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Document document = new Document(PageSize.A5, 42, 42, 42, 42);
            PdfWriter writer = PdfWriter.getInstance(document, out);
            document.open();
            BaseFont bf = BaseFont.createFont("STSong-Light", "UniGB-UCS2-H", BaseFont.NOT_EMBEDDED);
            Font title = new Font(bf, num(config, "titleSize", 18), Font.BOLD);
            Font normal = new Font(bf, 11);
            Font small = new Font(bf, 9);

            Paragraph titleParagraph = new Paragraph(text(config, "title", "电子收据"), title);
            titleParagraph.setAlignment(align(config));
            document.add(titleParagraph);
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
            Image seal = seal(config);
            if (seal != null) {
                seal.setAbsolutePosition(num(config, "sealX", 330), num(config, "sealY", 120));
                seal.scaleToFit(num(config, "sealSize", 90), num(config, "sealSize", 90));
                writer.getDirectContent().addImage(seal);
            }
            document.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new IllegalStateException("收据 PDF 生成失败", e);
        }
    }

    @SuppressWarnings("unchecked")
    private byte[] renderCanvas(Map<String, Object> receipt, Map<?, ?> canvas, Map<String, Object> config, String verifyUrl, String verifyCode) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Rectangle page = switch (String.valueOf(config == null ? "A4" : config.getOrDefault("pageSize", "A4"))) {
                case "A5" -> PageSize.A5;
                case "B5" -> new Rectangle(499, 709);
                default -> PageSize.A4;
            };
            if ("landscape".equalsIgnoreCase(String.valueOf(config == null ? "" : config.get("orientation")))) {
                page = new Rectangle(page.getHeight(), page.getWidth());
            }
            Document document = new Document(page, 0, 0, 0, 0);
            PdfWriter writer = PdfWriter.getInstance(document, out);
            document.open();
            document.add(new Paragraph(" "));
            document.newPage();
            PdfContentByte cb = writer.getDirectContent();
            BaseFont bf = BaseFont.createFont("STSong-Light", "UniGB-UCS2-H", BaseFont.NOT_EMBEDDED);
            float pageHeight = page.getHeight();
            Object objectsRaw = canvas.get("objects");
            if (objectsRaw instanceof java.util.List<?> objects) {
                for (Object raw : objects) {
                    if (!(raw instanceof Map<?, ?> obj)) continue;
                    String type = String.valueOf(obj.get("type"));
                    float left = f(obj.get("left"));
                    float top = f(obj.get("top"));
                    if ("textbox".equalsIgnoreCase(type) || "text".equalsIgnoreCase(type)) {
                        String text = replace(String.valueOf(obj.get("text") == null ? "" : obj.get("text")), receipt, config, verifyUrl, verifyCode);
                        float size = Math.max(6, f(obj.get("fontSize")));
                        cb.beginText();
                        cb.setFontAndSize(bf, size);
                        cb.setTextMatrix(left, pageHeight - top - size);
                        cb.showText(text);
                        cb.endText();
                    } else if ("image".equalsIgnoreCase(type)) {
                        String src = String.valueOf(obj.get("src"));
                        int comma = src.indexOf(',');
                        if (comma > 0) src = src.substring(comma + 1);
                        Image img = Image.getInstance(java.util.Base64.getDecoder().decode(src));
                        float width = f(obj.get("width")) * Math.max(1f, f(obj.get("scaleX")));
                        img.scaleToFit(width, 2000);
                        img.setAbsolutePosition(left, pageHeight - top - img.getScaledHeight());
                        cb.addImage(img);
                    } else if ("rect".equalsIgnoreCase(type) && ("qr".equalsIgnoreCase(String.valueOf(obj.get("role"))) || "#111".equalsIgnoreCase(String.valueOf(obj.get("fill"))))) {
                        float width = f(obj.get("width")) * Math.max(1f, f(obj.get("scaleX")));
                        Image qr = Image.getInstance(qrPng(verifyUrl, 180));
                        qr.scaleToFit(width, 2000);
                        qr.setAbsolutePosition(left, pageHeight - top - qr.getScaledHeight());
                        cb.addImage(qr);
                    }
                }
            }
            document.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new IllegalStateException("收据模板 PDF 生成失败", e);
        }
    }

    private float f(Object value) {
        if (value instanceof Number n) return n.floatValue();
        try { return value == null ? 0 : Float.parseFloat(String.valueOf(value)); } catch (Exception e) { return 0; }
    }

    private String replace(String text, Map<String, Object> receipt, Map<String, Object> config, String verifyUrl, String verifyCode) {
        return text.replace("{{receiptNo}}", value(receipt, "receiptNo"))
                .replace("{{paymentNo}}", value(receipt, "paymentNo"))
                .replace("{{amount}}", value(receipt, "amount"))
                .replace("{{paymentMethod}}", value(receipt, "paymentMethod"))
                .replace("{{issuedTime}}", value(receipt, "issuedTime"))
                .replace("{{receiptStatus}}", value(receipt, "receiptStatus"))
                .replace("{{status}}", value(receipt, "receiptStatus"))
                .replace("{{title}}", text(config, "title", "电子收据"))
                .replace("{{company}}", text(config, "company", "收款单位"))
                .replace("{{verifyCode}}", verifyCode)
                .replace("{{verifyUrl}}", verifyUrl);
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

    private int num(Map<String, Object> config, String key, int fallback) {
        Object v = config == null ? null : config.get(key);
        if (v instanceof Number n) return n.intValue();
        try { return v == null ? fallback : Integer.parseInt(String.valueOf(v)); } catch (Exception e) { return fallback; }
    }

    private int align(Map<String, Object> config) {
        String a = String.valueOf(config == null ? "center" : config.getOrDefault("titleAlign", "center"));
        return "left".equals(a) ? com.lowagie.text.Element.ALIGN_LEFT
                : "right".equals(a) ? com.lowagie.text.Element.ALIGN_RIGHT
                : com.lowagie.text.Element.ALIGN_CENTER;
    }

    private Image seal(Map<String, Object> config) {
        try {
            Object raw = config == null ? null : config.get("sealImage");
            if (raw == null || String.valueOf(raw).isBlank()) return null;
            String data = String.valueOf(raw);
            int comma = data.indexOf(',');
            if (comma >= 0) data = data.substring(comma + 1);
            return Image.getInstance(Base64.getDecoder().decode(data));
        } catch (Exception e) { return null; }
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
