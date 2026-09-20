import re

with open('onboarding.html', 'r') as f:
    content = f.read()

# First, remove old script if it exists
script_start = content.find('<script>\ndocument.addEventListener(\'DOMContentLoaded\', function() {\n    function updateTabStatus')
if script_start != -1:
    script_end = content.find('</script>\n\n{% endblock %}', script_start)
    if script_end != -1:
        content = content[:script_start] + "{% endblock %}"

script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    function updateTabStatus() {
        const panes = document.querySelectorAll('.ob-tab-pane');
        let allPanesValid = true;

        panes.forEach(pane => {
            const paneIdParts = pane.id.split('-');
            if (paneIdParts.length < 3) return;
            const tabName = paneIdParts[2];
            const tabBtn = document.getElementById('toptab-' + tabName);
            if (!tabBtn) return;

            let isValid = true;
            let hasRequired = false;

            if (tabName === 'apptype') {
                hasRequired = true;
                isValid = pane.querySelector('.ob-type-card--active') !== null;
            } else {
                const requiredFields = pane.querySelectorAll('input[required], select[required], textarea[required]');
                hasRequired = requiredFields.length > 0;
                
                if (tabName === 'optional') {
                    isValid = true;
                    hasRequired = true;
                } else {
                    requiredFields.forEach(field => {
                        if (field.type === 'radio' || field.type === 'checkbox') {
                            const name = field.name;
                            const checked = pane.querySelector(`input[name="${name}"]:checked`);
                            if (!checked) {
                                isValid = false;
                            }
                        } else if (field.type === 'file') {
                            if (!field.value) {
                                const parent = field.closest('.input-icon-wrap') || field.parentElement;
                                const hasExistingFile = parent.querySelector('a') !== null || parent.innerHTML.includes('Currently:');
                                if (!hasExistingFile) {
                                    isValid = false;
                                }
                            }
                        } else {
                            if (!field.value.trim()) {
                                isValid = false;
                            }
                        }
                    });
                }
            }

            let tickIcon = tabBtn.querySelector('.tab-completion-tick');
            if (isValid && hasRequired) {
                if (!tickIcon) {
                    tickIcon = document.createElement('i');
                    tickIcon.className = 'ri-checkbox-circle-fill text-success tab-completion-tick';
                    tickIcon.style.marginLeft = '4px';
                    tickIcon.style.fontSize = '1.05rem';
                    tickIcon.style.color = '#10b981'; 
                    tickIcon.style.opacity = '0';
                    tickIcon.style.transform = 'scale(0.5)';
                    tickIcon.style.transition = 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                    
                    const reqDot = tabBtn.querySelector('.req-dot');
                    if (reqDot) {
                        reqDot.style.display = 'none'; 
                        tabBtn.insertBefore(tickIcon, reqDot);
                    } else {
                        tabBtn.appendChild(tickIcon);
                    }
                    
                    setTimeout(() => {
                        tickIcon.style.opacity = '1';
                        tickIcon.style.transform = 'scale(1)';
                    }, 10);
                }
            } else {
                if (tickIcon) {
                    tickIcon.remove();
                    const reqDot = tabBtn.querySelector('.req-dot');
                    if (reqDot) {
                        reqDot.style.display = 'inline-block';
                    }
                }
                if (hasRequired) {
                    allPanesValid = false;
                }
            }
        });

        // Update active sidebar nav link badge
        const activeSidebarLink = document.querySelector('.ob-sidenav .nav-link.active');
        if (activeSidebarLink) {
            let badge = activeSidebarLink.querySelector('.nav-badge');
            if (badge) {
                if (allPanesValid) {
                    badge.innerHTML = '<i class="ri-check-double-line"></i> Done';
                    badge.className = 'nav-badge done';
                    badge.style.background = '#d1fae5';
                    badge.style.color = '#059669';
                } else {
                    badge.innerHTML = 'Now';
                    badge.className = 'nav-badge now';
                    badge.style.background = 'var(--teal-main)';
                    badge.style.color = '#fff';
                }
            }
        }
    }

    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('input', updateTabStatus);
        form.addEventListener('change', updateTabStatus);
        updateTabStatus();
    }
});
</script>
"""

content = content.replace("{% endblock %}", script + "\n{% endblock %}")
with open('onboarding.html', 'w') as f:
    f.write(content)
