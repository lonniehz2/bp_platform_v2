import io
p=r'src\main\java\com\yundao\platform\controller\AuthController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @GetMapping("/me")''','''    @PostMapping("/password")
    public R<Void> changePassword(@RequestBody AuthService.ChangePasswordCmd cmd) {
        authService.changePassword(cmd);
        return R.ok(null);
    }

    @GetMapping("/me")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('change password controller')
