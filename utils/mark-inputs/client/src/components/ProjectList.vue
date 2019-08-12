<template>
    <div>
        <div v-if="projects.length">
            <p>Choose a Project:</p>
            <ul id="project-list">
                    <Project
                    v-for="project in projects"
                    :key="project.id"
                    :project="project"
                    />
            </ul>
        </div>
        <div v-else>
            <p>{{ status }}</p>
        </div>
    </div>
</template>

<script>
import { Flywheel } from '../../services/Flywheel'
import Project from './Project.vue'

let fw;

export default {
    components: {
        Project
    },
    props: {
        fwApiKey: {
            type: String,
            required: true
        }
    },
    data() {
        return { projects: [], status: 'Loading projects...' }
    },
    created() {
        fw = new Flywheel(this.fwApiKey, process.env.VUE_APP_FW_URL)
        fw.getProjects()
        .then(res => this.projects = res)
        .catch(err => {
            console.log(err)
            this.status = 'Sorry, an error occurred. Please try again.'
        })
    }
}
</script>
    
<style>
    #project-list {
        list-style-type: none;
        margin-left: 100px;
        cursor: pointer;
    }
</style>