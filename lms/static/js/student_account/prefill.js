// Pre-fills form based on fields given by query
document.getElementById("login-and-registration-container").click();
// for every field in the query
var emailInputName = "register-email";
var emailInputName2 = "register-email_confirm";
var classCodeInputName = "register-class_code";
var typeInputName = "register-reg_type"


// Check if the administator only strictly wants the student to setup on their invited email.
var strict = getParameterByName("strict");


// Check for Class Code and email values
var regValue = getParameterByName("type");
var classCodeValue = getParameterByName("code");
var emailValue = getParameterByName("email");

if (regValue!=false){
    var regField = document.getElementById(typeInputName);
    regField.value = regValue;
    $("#"+typeInputName).change();
    regField.style.display = "none";
    if(regValue==1){
        regText="   Student";
    }
    else if (regValue==2){
        regText="   Teacher";
    }
    regField.parentElement.innerHTML=regField.parentElement.innerHTML + "<span style='font-size:10pt'>"+ regText+ "</span>";
}

if (classCodeValue!=false){
    var classCodeField = document.getElementById(classCodeInputName);
    classCodeField.value = classCodeValue;
    classCodeField.readOnly = true;
    classCodeField.style.backgroundColor = "#EEE";
    document.getElementById("register-class_code-desc").innerHTML="This has been pre-filled in for you.";
}


if (emailValue!=false){
    var emailField = document.getElementById(emailInputName);
    emailField.value = emailValue;

    if (strict){
        emailField.readOnly = true;
        emailField.style.backgroundColor = "#EEE";
        document.getElementById("register-email-desc").innerHTML="Your teacher has requested you use this e-mail address.";
    }
}

function getParameterByName(name)
{
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.href);
    if (results == null) return false;
    else return decodeURIComponent(results[1].replace(/\+/g, " "));
}

