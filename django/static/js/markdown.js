function jsonEditor() {
    return {
        content: {
            question_text: "",
            all_or_nothing: false,
            choices: [{ score: 1, text: "" },],
            multiple_selections: false,
            description:""
        },
        questionEditor: null,
        description:null,
        choiceEditors: [],
        
        init() {
            this.initQuestionEditor();
            this.initdescription();
            this.initChoiceEditors();
        },

        initQuestionEditor() {
            this.questionEditor = new toastui.Editor({
                el: document.querySelector("#questionEditor"),
                height: "250px",
                initialEditType: "markdown",
                previewStyle: "tab",
                initialValue: this.content.question_text,
                events: {
                    change: () => {
                        this.content.question_text = this.questionEditor.getMarkdown();
                    }
                }
            });
        },
        initdescription() {
            this.description = new toastui.Editor({
                el: document.querySelector("#description"),
                height: "250px",
                initialEditType: "markdown",
                previewStyle: "tab",
                initialValue: this.content.description,
                events: {
                    change: () => {
                        this.content.description = this.description.getMarkdown();
                    }
                }
            });
        },

        initChoiceEditors() {
            this.choiceEditors = [];
            this.content.choices.forEach((choice, index) => {
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
                    initialEditType: "wysiwyg",
                    previewStyle: "tab",
                    initialValue: text,
                    events: {
                        change: () => {
                            this.content.choices[index].text = this.choiceEditors[index].getMarkdown();
                        }
                    }
                });
            }, 100);
        },

        addChoice() {
            this.content.choices.push({ score: 0, text: "" });
            let index = this.content.choices.length - 1;
            this.$nextTick(() => this.createChoiceEditor(index, ""));
        },

        removeChoice(index) {
            this.content.choices.splice(index, 1);
            this.choiceEditors.splice(index, 1);
        }
    };
}
