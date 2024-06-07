
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

select.addEventListener("change", (event) => {
  if(event.target.value === "2"){
    tema.setAttribute("href", "https://bootswatch.com/5/cosmo/bootstrap.min.css");  
  }
  else{
    tema.setAttribute("href", "https://bootswatch.com/5/darkly/bootstrap.min.css");  
  }
});
