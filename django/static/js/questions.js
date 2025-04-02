document.addEventListener("alpine:init", () => {
    Alpine.data("questionsTable", () => ({
        questions: [],
        questionTypes: [],
        tags: [], 
        statuses: ["draft", "published", "inactive", "closed"],
        selectedStatus: "draft",
        currentQuestion: getDefaultQuestion(),
        showModal: false,
        isEditing: false,
        contentError: null,
        currentPage: 1,
        pageSize: 10,
        authHeaders: {
            "Authorization": "Basic " + btoa("admin:admin"),
            "Content-Type": "application/json"
        },
        questionEditor: null,
        choiceEditors: [],

        init() {
            this.initQuestionEditor();
            this.initChoiceEditors();
        },

        initQuestionEditor() {
            try {
                if (this.questionEditor) {
                    this.questionEditor.destroy();
                }
            } catch (error) {
                console.error("Error destroying question editor:", error);
            }

            this.questionEditor = new toastui.Editor({
                el: document.querySelector("#questionEditor"),
                height: "250px",
                initialEditType: "markdown",
                previewStyle: "tab",
                initialValue: this.currentQuestion.content.question_text,
                events: {
                    change: () => {
                        this.currentQuestion.content.question_text = this.questionEditor.getMarkdown();
                    }
                }
            });
        },

        initChoiceEditors() {
            this.choiceEditors.forEach(editor => {
                if (editor) {
                    try {
                        editor.destroy();
                    } catch (error) {
                        console.error("Error destroying choice editor:", error);
                    }
                }
            });
            this.choiceEditors = [];
            this.currentQuestion.content.choices.forEach((choice, index) => {
                this.createChoiceEditor(index, choice.text);
            });
        },

        createChoiceEditor(index, text) {
            setTimeout(() => {
                let editorElement = document.querySelector(`#choiceEditor${index}`);
                if (!editorElement) return;

                this.choiceEditors[index] = new toastui.Editor({
                    el: editorElement,
                    height: "100px",
                    initialEditType: "markdown",
                    previewStyle: "tab",
                    initialValue: text,
                    events: {
                        change: () => {
                            this.currentQuestion.content.choices[index].text = this.choiceEditors[index].getMarkdown();
                        }
                    }
                });
            }, 100);
        },

        addChoice() {
            this.currentQuestion.content.choices.push({ score: 0, text: "" });
            let index = this.currentQuestion.content.choices.length - 1;
            this.$nextTick(() => this.createChoiceEditor(index, ""));
        },

        removeChoice(index) {
            this.currentQuestion.content.choices.splice(index, 1);
            this.choiceEditors.splice(index, 1);
        },

        async fetchData() {
            try {
                let [questionsRes, typesRes, tagsRes] = await Promise.all([
                    fetch("/questions/", { headers: this.authHeaders }),
                    fetch("/question-types/", { headers: this.authHeaders }),
                    fetch("/tags/", { headers: this.authHeaders })
                ]);

                if (!questionsRes.ok || !typesRes.ok || !tagsRes.ok) throw new Error("Failed to fetch data");

                this.questions = await questionsRes.json();
                this.questionTypes = await typesRes.json();
                this.tags = await tagsRes.json();

                this.questions.sort((a, b) => b.id - a.id);

            } catch (err) {
                console.log(err);
            }
        },

        get totalPages() {
            return Math.ceil(this.questions.length / this.pageSize);
        },

        get paginatedQuestions() {
            let start = (this.currentPage - 1) * this.pageSize;
            let end = start + this.pageSize;
            return this.questions.slice(start, end);
        },

        prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
            }
        },

        nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
            }
        },

        validateJSON(content) {
            try {
                if (typeof content === "string") {
                    JSON.parse(content);
                }
                this.contentError = null;
                return true;
            } catch {
                this.contentError = "Invalid JSON format!";
                return false;
            }
        },

        updateSelectedTags(event) {
            let selectedOptions = [...event.target.selectedOptions].map(opt => parseInt(opt.value));
            this.currentQuestion.tags = selectedOptions;
        },

        openAddModal() {
            this.currentQuestion = getDefaultQuestion();
            this.isEditing = false;
            this.showModal = true;
            this.$nextTick(() => {
                this.initQuestionEditor();
                this.initChoiceEditors();
            });
        },

        async openEditModal(question) {
            try {
                this.currentQuestion = getDefaultQuestion();
                let response = await fetch(`/questions/${question.uid}/${question.revision_id}/`, { headers: this.authHeaders });
                if (!response.ok) throw new Error("Failed to fetch question details");

                let data = await response.json();
                this.isEditing = true;
                this.currentQuestion.id = data.id;
                this.currentQuestion.uid = data.uid;
                this.currentQuestion.revision_id = data.revision_id;
                this.currentQuestion.question_type = data.question_type.id;
                this.currentQuestion.copied_from = data.copied_from;
                this.currentQuestion.status = data.status;
                this.currentQuestion.tags = data.tags.map(tag => tag.id);
                this.currentQuestion.content = data.content;

                this.showModal = true;
                this.$nextTick(() => {
                    this.initQuestionEditor();
                    this.initChoiceEditors();
                });
            } catch (err) {
                console.error("Error fetching question:", err);
                alert("Failed to load question details. Please try again.");
            }
        },

        async cancelSave() {
            this.showModal = false;
        },

        async saveQuestion() {
            if (!this.validateJSON(JSON.stringify(this.currentQuestion.content, null, 2))) return;
            let url = this.isEditing ? `/questions/${this.currentQuestion.uid}/${this.currentQuestion.revision_id}/` : "/questions/";
            let method = this.isEditing ? "PUT" : "POST";

            let payload = {
                ...(this.isEditing && { id: this.currentQuestion.id }),
                uid: this.currentQuestion.uid,
                revision_id: this.currentQuestion.revision_id,
                question_type: this.currentQuestion.question_type,
                copied_from: this.currentQuestion.copied_from,
                status: this.currentQuestion.status,
                tags: this.currentQuestion.tags,
                content: this.currentQuestion.content
            };

            try {
                let response = await fetch(url, {
                    method: method,
                    headers: this.authHeaders,
                    body: JSON.stringify(payload, null, 2)
                });
                if (!response.ok) {
                    alert("Failed to save question: " + response.statusText);
                    throw new Error("Failed to save question");
                }

                await this.fetchData();
                this.showModal = false;
            } catch (err) {
                console.log(err);
            }
        }
    }));

    function getDefaultQuestion() {
        return {
            uid: '',
            revision_id: 1,
            question_type: 1,
            copied_from: '',
            status: 'draft',
            tags: [],
            content: {
                all_or_nothing_grading: false,
                choices: [],
                multiple_selections: false,
                question_text: ""
            }
        };
    }
});