(function () {
    const api = {
        postForm: function postForm(url, formElement) {
            return fetch(url, {
                method: "POST",
                body: new FormData(formElement),
            });
        },

        postFormData: function postFormData(url, formData) {
            return fetch(url, {
                method: "POST",
                body: formData,
            });
        },

        parseJsonSafe: async function parseJsonSafe(response) {
            try {
                return await response.json();
            } catch (_error) {
                return null;
            }
        },
    };

    window.forms = api;
})();
