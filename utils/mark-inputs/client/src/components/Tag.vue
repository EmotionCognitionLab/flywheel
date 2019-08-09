<template>
    <div v-if="allTags.length">
        <TaggedFiles v-for="(taggedFiles, index) in allTags"
        :key="index"
        :files=taggedFiles.files
        :initialTag=taggedFiles.tag
        @tag-list-changed="onTagListChanged"
        >

        </TaggedFiles>
        <router-link :to="{ name: 'project', params: { id: projectId }}" class="taglink" id="tag-more"> &lt;&lt; Tag more files</router-link>
        <router-link :to="{ name: 'upload', params: { projectId: projectId, projectLabel: projectLabel}}" class="taglink">Save and Finish &gt;&gt;</router-link>
        
    </div>
    <div v-else>
        You must <router-link :to="{ name: 'project', params: { id: projectId }}">select some files.</router-link>
    </div>
</template>

<script>
import TaggedFiles from './TaggedFiles'
import TagManager from '../../services/TagManager'

export default {
    components: { TaggedFiles },
    beforeRouteLeave(to, from, next) {
        if (this.hasUntaggedFiles()) {
            const ans = window.confirm("Leaving the page without providing a tag for selected files may cause your file selections to be lost. Are you sure you want to do that?")
            if (ans) {
                next()
            } else {
                next(false)
            }
        } else {
            next()
        }
    },
    created() {
        if (this.selectedFiles.length) {
            TagManager.save({ tag: '', files: this.selectedFiles })
        }
        this.allTags = TagManager.getAllTags()
    },
    data() {
        return {
            allTags: {}
        }
    },
    methods: {
        hasUntaggedFiles: function() {
            var res = false
            for (var i = 0; i < this.allTags.length; i++) {
                if (!this.allTags[i].tag) res = true;
            }
            return res
        },
        onTagListChanged: function() {
            this.allTags = TagManager.getAllTags()
        }
    },
    props: {
        projectId: {
            type: String,
            required: true
        },
        projectLabel: {
            type: String,
            required: true
        },
        selectedFiles: {
            type: Array,
            required: true
        }
    }
}
</script>
<style>
    #tag-more {
        float: left;
    }
</style>