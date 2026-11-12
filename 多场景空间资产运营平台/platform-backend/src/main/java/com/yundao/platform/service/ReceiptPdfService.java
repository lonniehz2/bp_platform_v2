package com.yundao.platform.service;

import com.lowagie.text.Document;
import com.lowagie.text.Font;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfWriter;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class ReceiptPdfService {

    public byte[] render(Map<String, Object> receipt) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Document document = new Document(PageSize.A5, 42, 42, 42, 42);
            PdfWriter.getInstance(document, out);
            document.open();
            BaseFont bf = BaseFont.createFont("STSong-Light", "UniGB-UCS2-H", BaseFont.NOT_EMBEDDED);
            Font title = new Font(bf, 18, Font.BOLD);
            Font normal = new Font(bf, 11);
            Font small = new Font(bf, 9);

            document.add(new Paragraph("电子收据", title));
            document.add(new Paragraph("ELECTRONIC RECEIPT", small));
            document.add(new Paragraph(" "));
            document.add(new Paragraph("收据编号 / Receipt No: " + value(receipt, "receiptNo"), normal));
            document.add(new Paragraph("付款编号 / Payment No: " + value(receipt, "paymentNo"), normal));
            document.add(new Paragraph("付款金额 / Amount: CNY " + value(receipt, "amount"), normal));
            document.add(new Paragraph("付款方式 / Method: " + value(receipt, "paymentMethod"), normal));
            document.add(new Paragraph("开具时间 / Issued At: " + value(receipt, "issuedTime"), normal));
            document.add(new Paragraph("状态 / Status: " + value(receipt, "receiptStatus"), normal));
            document.add(new Paragraph(" "));
            document.add(new Paragraph("验真码 / Verify Code: " + verifyCode(receipt), small));
            document.add(new Paragraph("本收据为电子收款凭证，可在业务平台核对。", small));
            document.add(new Paragraph("This is an electronic payment receipt.", small));
            document.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new IllegalStateException("收据 PDF 生成失败", e);
        }
    }

    private String value(Map<String, Object> receipt, String key) {
        Object v = receipt.get(key);
        return v == null ? "-" : String.valueOf(v);
    }

    private String verifyCode(Map<String, Object> receipt) {
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
}
