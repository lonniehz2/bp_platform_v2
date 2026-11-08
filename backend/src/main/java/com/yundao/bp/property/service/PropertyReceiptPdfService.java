package com.yundao.bp.property.service;

import com.lowagie.text.Document;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import java.io.ByteArrayOutputStream;
import java.math.BigDecimal;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/** 生成物业电子收据 PDF。 */
@Service
public class PropertyReceiptPdfService {

    private final JdbcTemplate jdbc;
    private final String fontPath;

    public PropertyReceiptPdfService(JdbcTemplate jdbc,
            @Value("${bp.property.receipt-font:/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc,0}")
            String fontPath) {
        this.jdbc = jdbc;
        this.fontPath = fontPath;
    }

    public byte[] render(Long receiptId) {
        Map<String, Object> r = jdbc.query(
                "select r.receipt_no, r.payer_name, r.amount, r.issued_at, p.payment_no, "
                        + "p.pay_channel, p.pay_time, pc.project_name, pc.receipt_header "
                        + "from prop_receipt r join prop_payment p on p.id=r.payment_id "
                        + "left join prop_project_config pc on pc.org_id=r.project_id "
                        + "where r.id=? and r.tenant_id=?",
                rs -> {
                    if (!rs.next()) return null;
                    Map<String, Object> m = new java.util.LinkedHashMap<>();
                    m.put("receiptNo", rs.getString("receipt_no"));
                    m.put("payerName", rs.getString("payer_name"));
                    m.put("amount", rs.getBigDecimal("amount"));
                    m.put("issuedAt", rs.getTimestamp("issued_at"));
                    m.put("paymentNo", rs.getString("payment_no"));
                    m.put("payChannel", rs.getString("pay_channel"));
                    m.put("payTime", rs.getTimestamp("pay_time"));
                    m.put("projectName", rs.getString("project_name"));
                    m.put("receiptHeader", rs.getString("receipt_header"));
                    return m;
                }, receiptId, TenantContext.tenantId());
        if (r == null) {
            throw BizException.notFound("电子收据");
        }
        try {
            BaseFont bf = BaseFont.createFont(fontPath, BaseFont.IDENTITY_H, BaseFont.EMBEDDED);
            Font titleFont = new Font(bf, 18, Font.BOLD);
            Font headFont = new Font(bf, 11, Font.BOLD);
            Font normal = new Font(bf, 10, Font.NORMAL);
            Font small = new Font(bf, 9, Font.NORMAL);

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Document doc = new Document(PageSize.A5, 36, 36, 30, 30);
            PdfWriter.getInstance(doc, out);
            doc.open();
            Paragraph title = new Paragraph("电子收据", titleFont);
            title.setAlignment(Element.ALIGN_CENTER);
            doc.add(title);
            Paragraph sub = new Paragraph(String.valueOf(r.get("receiptHeader") == null
                    ? r.get("projectName") : r.get("receiptHeader")), normal);
            sub.setAlignment(Element.ALIGN_CENTER);
            doc.add(sub);
            doc.add(new Paragraph(" "));
            doc.add(line("收据编号", str(pick(r,"receiptNo","receipt_no")), normal));
            doc.add(line("项目名称", str(pick(r,"projectName","project_name")), normal));
            doc.add(line("付款人", str(pick(r,"payerName","payer_name")), normal));
            doc.add(line("收款金额", "￥" + pick(r,"amount","amount"), headFont));
            doc.add(line("收款方式", str(pick(r,"payChannel","pay_channel")), normal));
            doc.add(line("收款时间", str(pick(r,"payTime","pay_time")), normal));
            doc.add(line("支付流水号", str(pick(r,"paymentNo","payment_no")), small));
            doc.add(new Paragraph(" "));

            PdfPTable table = new PdfPTable(new float[]{2.2f, 1.8f, 1.4f, 1.3f});
            table.setWidthPercentage(100);
            addHead(table, "账单编号", headFont);
            addHead(table, "计费期间", headFont);
            addHead(table, "收费项目", headFont);
            addHead(table, "金额", headFont);
            List<Map<String, Object>> bills = jdbc.query(
                    "select b.bill_no, b.period_start, b.period_end, b.payable_amount, "
                            + "f.fee_item_name from prop_payment_allocation a "
                            + "join prop_bill b on b.id=a.bill_id "
                            + "left join prop_fee_item f on f.id=b.fee_item_id "
                            + "where a.payment_id=(select payment_id from prop_receipt where id=?) order by b.id",
                    (rs, rowNum) -> {
                        Map<String, Object> m = new java.util.LinkedHashMap<>();
                        m.put("billNo", rs.getString("bill_no"));
                        m.put("periodStart", rs.getDate("period_start"));
                        m.put("periodEnd", rs.getDate("period_end"));
                        m.put("amount", rs.getBigDecimal("payable_amount"));
                        m.put("feeItemName", rs.getString("fee_item_name"));
                        return m;
                    }, receiptId);
            for (Map<String, Object> b : bills) {
                cell(table, str(pick(b,"billNo","bill_no")), normal);
                cell(table, str(pick(b,"periodStart","period_start")) + " ~ " + str(pick(b,"periodEnd","period_end")), normal);
                cell(table, str(pick(b,"feeItemName","fee_item_name")), normal);
                cell(table, "￥" + pick(b,"amount","amount"), normal);
            }
            doc.add(table);
            doc.add(new Paragraph(" "));
            Paragraph note = new Paragraph("本收据为电子收据，可在智慧物业系统中验真。", small);
            note.setAlignment(Element.ALIGN_CENTER);
            doc.add(note);
            doc.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.SYSTEM_ERROR,
                    "收据 PDF 生成失败：" + e.getMessage());
        }
    }

    private static Paragraph line(String label, String value, Font font) {
        Paragraph p = new Paragraph(label + "：" + (value == null ? "-" : value), font);
        p.setSpacingAfter(4);
        return p;
    }

    private static void addHead(PdfPTable table, String text, Font font) {
        PdfPCell cell = new PdfPCell(new Paragraph(text, font));
        cell.setHorizontalAlignment(Element.ALIGN_CENTER);
        cell.setPadding(5);
        table.addCell(cell);
    }

    private static void cell(PdfPTable table, String text, Font font) {
        PdfPCell cell = new PdfPCell(new Paragraph(text == null ? "-" : text, font));
        cell.setPadding(5);
        table.addCell(cell);
    }

    private static Object pick(Map<String, Object> row, String camel, String snake) {
        Object v = row.get(camel);
        return v != null ? v : row.get(snake);
    }

    private static String str(Object v) {
        return v == null ? "" : String.valueOf(v);
    }
}
