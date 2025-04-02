document.addEventListener("alpine:init", () => {
    Alpine.data("fileUploader", () => ({
        file: null,
        resourceId: "",  // Input for resource ID
        message: "",

        handleFile(event) {
            this.file = event.target.files[0];
            console.log("Selected file:", this.file);
        },

        async uploadFile() {
            if (!this.file || !this.resourceId) {
                this.message = "Please select a file and enter Resource ID!";
                return;
            }

            let formData = new FormData();
            formData.append("file", this.file);
            formData.append("resource_id", this.resourceId);  // Attach resource ID

            try {
                let response = await fetch("/assets/", {  // Changed endpoint
                    method: "POST",
                    body: formData
                });

                let data = await response.json();
                if (response.ok) {
                    this.message = `Uploaded! File ID: ${data.file_id}`;
                    console.log("File uploaded successfully:", data);
                } else {
                    this.message = `Error: ${data.detail}`;
                }
            } catch (error) {
                console.error("Upload failed:", error);
                this.message = "Upload failed!";
            }
        }
    }));

    Alpine.data("fileLoader", () => ({
        fileId: "",
        fileUrl: "",
        fileType: "",
        message: "",

        async fetchFile() {
            if (!this.fileId) {
                this.message = "Please enter a file ID!";
                return;
            }

            try {
                let response = await fetch(`/assets/${this.fileId}/`);  
                if (!response.ok) {
                    this.message = "File not found!";
                    this.fileUrl = "";
                    return;
                }
                console.log("response:",response)
                let blob = await response.blob();
                this.fileType = blob.type;
                this.fileUrl = URL.createObjectURL(blob);  
                this.message = "";

                console.log("Loaded file:", this.fileUrl, "Type:", this.fileType);
            } catch (error) {
                console.error("Error loading file:", error);
                this.message = "Failed to load file!";
                this.fileUrl = "";  
            }
        }
    }));
});
