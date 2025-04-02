document.addEventListener("alpine:init", () => {
    Alpine.data("questionTypesStore", () => ({
        questionTypes: [],
        newQuestionType: { qtype_id: "", description: "", how_to: "" },
        editingId: null,

        fetchQuestionTypes() {
            fetch("/question-types/")
                .then((res) => res.json())
                .then((data) => (this.questionTypes = data))
                .catch((err) => console.error(err));
        },

        addQuestionType() {
            fetch("/question-types/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.newQuestionType),
            })
                .then((res) => res.json())
                .then((data) => {
                    this.questionTypes.push(data);
                    this.newQuestionType = { qtype_id: "", description: "", how_to: "" };
                })
                .catch((err) => console.error(err));
        },

        updateQuestionType(qt) {
            fetch(`/question-types/${qt.id}/`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(qt),
            })
                .then(() => (this.editingId = null))
                .catch((err) => console.error(err));
        },
    }));
});
