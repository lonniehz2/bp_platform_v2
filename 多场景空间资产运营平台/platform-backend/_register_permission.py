import io
p=r'src\main\java\com\yundao\platform\config\WebConfig.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;''','''import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;''')
s=s.replace('''public class WebConfig implements WebMvcConfigurer {''','''public class WebConfig implements WebMvcConfigurer {

    private final PermissionInterceptor permissionInterceptor;

    public WebConfig(PermissionInterceptor permissionInterceptor) {
        this.permissionInterceptor = permissionInterceptor;
    }''')
s=s.replace('''    @Override
    public void addCorsMappings(CorsRegistry registry) {''','''    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(permissionInterceptor).addPathPatterns("/api/v1/platform/**");
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('interceptor registered')
