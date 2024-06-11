function getCookie(name) 
{
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function setCookie(name, value, days) 
{
	var expires = "";
	if (days) 
	{
    	var date = new Date();
    	date.setTime(date.getTime() + (days*24*60*60*1000));
    	expires = "; expires=" + date.toUTCString();
	}

	document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

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

function set_tema(id_tema)
{
  if(id_tema === "2")
  {
    tema.setAttribute("href", "https://bootswatch.com/5/darkly/bootstrap.min.css");  
    setCookie("tema", "2", 1)
  }
  else
  {
    tema.setAttribute("href", "https://bootswatch.com/5/cosmo/bootstrap.min.css");  
    setCookie("tema", "1", 1)
  }
}

select.addEventListener("change", (event) => {
  set_tema(event.target.value)
});

document.addEventListener("DOMContentLoaded", function() 
{
  set_tema( getCookie("tema") )
});