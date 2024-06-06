
const btnDelete= document.querySelectorAll('.btn-borrar');
if(btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('¿Está seguro de querer borrar?')){
        e.preventDefault();
      }
    });
  })
}

const select = document.getElementById("selector_tema");
const tema = document.getElementById("tema");
//    document.getElementById("pagestyle").setAttribute("href", sheet);  

select.addEventListener("change", (event) => {
  result.textContent = `You like ${event.target.value}`;
});
