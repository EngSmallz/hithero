(function () {
    window.updateCharacterCount = function updateCharacterCount() {
        const messageElement = document.getElementById("message");
        const countElement = document.getElementById("charCount");
        if (messageElement && countElement) {
            const charsRemaining = 250 - messageElement.value.length;
            countElement.textContent = charsRemaining + " characters remaining";
        }
    };

    document.addEventListener("DOMContentLoaded", function () {
        updateCharacterCount();
        checkAuthentication();

        const contactForm = document.getElementById("contact-form");
        const submitButton = document.getElementById("submitButton");
        const contactMessageDiv = document.getElementById("contact-message");

        if (!contactForm) {
            console.error("DEBUG: 'contact-form' ID not found in HTML!");
        }
        if (!submitButton) {
            console.error("DEBUG: 'submitButton' ID not found in HTML!");
        }

        if (contactForm && submitButton) {
            submitButton.addEventListener("click", async function (event) {
                event.preventDefault();

                contactMessageDiv.textContent = "Sending your message...";
                contactMessageDiv.style.color = "#10B981";
                submitButton.disabled = true;

                const formData = new FormData(contactForm);
                let recaptchaResponse = "";

                if (typeof grecaptcha !== "undefined" && grecaptcha.getResponse) {
                    recaptchaResponse = grecaptcha.getResponse();
                }

                if (!recaptchaResponse) {
                    contactMessageDiv.textContent = "Please complete the reCAPTCHA to send your message.";
                    contactMessageDiv.style.color = "orange";
                    submitButton.disabled = false;
                    grecaptcha.reset();
                    return;
                }

                formData.append("recaptcha_response", recaptchaResponse);

                try {
                    const response = await fetch("/api/contact_us/", {
                        method: "POST",
                        body: formData,
                    });
                    const responseData = await response.json();

                    if (response.ok) {
                        contactMessageDiv.textContent = responseData.message || "Message sent successfully!";
                        contactMessageDiv.style.color = "#10B981";
                        contactForm.reset();
                        updateCharacterCount();
                        grecaptcha.reset();
                    } else {
                        const errorMessage = responseData.message || responseData.detail || "Message submission failed. Please try again.";
                        contactMessageDiv.textContent = errorMessage;
                        contactMessageDiv.style.color = "red";
                        grecaptcha.reset();
                    }
                } catch (error) {
                    console.error("Error submitting form:", error);
                    contactMessageDiv.textContent = "An error occurred. Please try again.";
                    contactMessageDiv.style.color = "red";
                    grecaptcha.reset();
                } finally {
                    submitButton.disabled = false;
                }
            });
        }
    });
})();
