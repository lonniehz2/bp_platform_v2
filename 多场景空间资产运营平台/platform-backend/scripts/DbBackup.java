import java.io.BufferedWriter;
import java.io.FileWriter;
import java.sql.*;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * 无 mysqldump 环境下的最小数据库逻辑备份工具。
 * 用法：java -cp mysql-connector-j.jar:. DbBackup host port user password db out.sql
 */
public class DbBackup {
    public static void main(String[] args) throws Exception {
        if (args.length < 6) {
            System.err.println("usage: DbBackup host port user password db out.sql");
            System.exit(2);
        }
        String url = "jdbc:mysql://" + args[0] + ":" + args[1] + "/" + args[4]
                + "?useSSL=false&allowPublicKeyRetrieval=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai";
        try (Connection c = DriverManager.getConnection(url, args[2], args[3]);
             BufferedWriter out = new BufferedWriter(new FileWriter(args[5]))) {
            out.write("SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n\n");
            List<String> tables = new ArrayList<>();
            try (Statement st = c.createStatement();
                 ResultSet rs = st.executeQuery("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")) {
                while (rs.next()) tables.add(rs.getString(1));
            }
            for (String table : tables) {
                String quoted = "`" + table.replace("`", "``") + "`";
                String ddl;
                try (Statement st = c.createStatement(); ResultSet rs = st.executeQuery("SHOW CREATE TABLE " + quoted)) {
                    rs.next();
                    ddl = rs.getString(2);
                }
                out.write("DROP TABLE IF EXISTS " + quoted + ";\n" + ddl + ";\n");
                try (Statement st = c.createStatement(); ResultSet rs = st.executeQuery("SELECT * FROM " + quoted)) {
                    ResultSetMetaData md = rs.getMetaData();
                    int n = md.getColumnCount();
                    StringBuilder head = new StringBuilder("INSERT INTO " + quoted + " (");
                    for (int i = 1; i <= n; i++) {
                        if (i > 1) head.append(',');
                        head.append('`').append(md.getColumnName(i).replace("`", "``")).append('`');
                    }
                    head.append(") VALUES ");
                    long count = 0;
                    while (rs.next()) {
                        if (count % 500 == 0) {
                            if (count > 0) out.write(";\n");
                            out.write(head.toString());
                        } else {
                            out.write(",\n");
                        }
                        out.write("(");
                        for (int i = 1; i <= n; i++) {
                            if (i > 1) out.write(',');
                            out.write(sqlValue(rs.getObject(i)));
                        }
                        out.write(")");
                        count++;
                    }
                    if (count > 0) out.write(";\n");
                }
                out.write("\n");
            }
            out.write("SET FOREIGN_KEY_CHECKS=1;\n");
        }
    }

    private static String sqlValue(Object v) {
        if (v == null) return "NULL";
        if (v instanceof Number || v instanceof Boolean) return v.toString();
        if (v instanceof byte[] bytes) {
            StringBuilder hex = new StringBuilder("0x");
            for (byte b : bytes) hex.append(String.format("%02x", b));
            return hex.toString();
        }
        String s;
        if (v instanceof Timestamp ts) s = ts.toLocalDateTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        else if (v instanceof Date d) s = d.toString();
        else if (v instanceof Time t) s = t.toString();
        else s = v.toString();
        return "'" + s.replace("\\", "\\\\").replace("'", "''").replace("\n", "\\n").replace("\r", "\\r") + "'";
    }
}
