(function() {
  function save(val) {
    try { localStorage.setItem('mcp_suffix', val); } catch(e) {}
  }
  function load() {
    try { return localStorage.getItem('mcp_suffix') || ''; } catch(e) { return ''; }
  }
  function apply(val) {
    document.querySelectorAll('[data-suffix-bind]')
      .forEach(function(el){
        var template = el.getAttribute('data-template');
        if (!template) return;
        el.textContent = template.replace(/<SUFFIX>/g, val || 'YOURSUFFIX');
      });
    document.querySelectorAll('code[data-template]')
      .forEach(function(el){
        var template = el.getAttribute('data-template');
        el.textContent = template.replace(/<SUFFIX>/g, val || 'YOURSUFFIX');
      });
  }
  function init() {
    var input = document.getElementById('suffix-input');
    if (!input) return;
    var v = load();
    if (v) input.value = v;
    apply(v);
    input.addEventListener('input', function(){
      save(this.value.trim());
      apply(this.value.trim());
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})();
