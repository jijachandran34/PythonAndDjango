
document.addEventListener("alpine:init", () => {
    Alpine.data("tagsTable", () => ({
        tags: [],
        newTag: { key: '', value: '' }, // Form Data
        loading: true,
        error: null,

        async fetchData() {
            try {
                this.loading = true;
                this.error = null;
                let response = await fetch("/tags/");
                if (!response.ok) throw new Error("Failed to fetch tags");
                this.tags = await response.json();
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async addTag() {
            try {
                let response = await fetch("/tags/", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "Authorization": "Basic " + btoa("admin:admin") 
                    },
                    body: JSON.stringify(this.newTag)
                });
                if (!response.ok) throw new Error("Failed to add tag");

                let newTag = await response.json();
                this.tags.push(newTag);
                this.newTag = { key: '', value: '' }; // Reset form
            } catch (err) {
                this.error = err.message;
            }
        },
    }));
});
