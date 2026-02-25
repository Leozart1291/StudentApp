document.addEventListener('DOMContentLoaded', function() {
    const button = document.getElementById('clickBtn');
    const message = document.getElementById('message');
    
    button.addEventListener('click', function() {
        message.textContent = 'Кнопка была нажата!';
        message.style.color = '#764ba2';
        
        setTimeout(function() {
            message.textContent = '';
        }, 3000);
    });
});
