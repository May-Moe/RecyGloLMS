

//show password
document.getElementById('show-password').addEventListener('change', function() {
var passwordField = document.getElementById('password');
if (this.checked) {
    passwordField.type = 'text';
} else {
    passwordField.type = 'password';
}
});

//forgot passwsord
document.getElementById('forgot-password').addEventListener('click', function() {
    document.getElementById('overlay').classList.add('active');
});

//close forgot password
document.getElementById('close-icon').addEventListener('click', function() {
    document.getElementById('overlay').classList.remove('active');
});
