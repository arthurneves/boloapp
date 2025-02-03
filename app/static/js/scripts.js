document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    navbarToggler.addEventListener('click', function() {
        navbarCollapse.classList.toggle('show');
    });

    // Handle dropdown toggles
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Close other dropdowns
            dropdownToggles.forEach(otherToggle => {
                if (otherToggle !== toggle) {
                    otherToggle.parentElement.querySelector('.dropdown-menu').classList.remove('show');
                }
            });

            // Toggle current dropdown
            const dropdownMenu = this.parentElement.querySelector('.dropdown-menu');
            dropdownMenu.classList.toggle('show');
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navbarCollapse.classList.contains('show') && 
            !e.target.closest('.navbar-collapse') && 
            !e.target.closest('.navbar-toggler')) {
            navbarCollapse.classList.remove('show');
        }
    });




    // Colapsar elementos
    const botoesColapsaveis = document.querySelectorAll('.botao-colapsavel');

    botoesColapsaveis.forEach(botao => {
        botao.addEventListener('click', () => {
            
            const targetId = botao.dataset.target;
            const elementoColapsavel = document.getElementById(targetId);
            elementoColapsavel.classList.toggle('colapsado');

            // Adiciona/remove a classe 'ativo' no botão
            botao.classList.toggle('ativo'); 
        });
    });

});



