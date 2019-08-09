const axios = require('axios');

class Flywheel {
    constructor(apiKey, apiUrl) {
        this.api = axios.create({
            baseURL: apiUrl,
            headers: { "X-FW-API-KEY": apiKey}
        });
    }

    async getProjects() {
        const projects = await this.api.get('/projects', this.default_headers);
        return projects.data;
    }

    async getProject(id) {
        const project = await this.api.get('/projects/'+id, this.default_headers);
        return project.data;
    }

    async uploadFileToProject(id, fileName, fileContents, contentType) {
        const body = {
            name: fileName,
            content: fileContents,
            contentType: contentType
        };
        
        await this.api.post(`/projects/${id}/file/upload`, JSON.stringify(body), {headers: {"Content-Type": "application/json"}});
        return '{}'
    }
}


export { Flywheel };