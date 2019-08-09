<template>
    <div>
        <h2>{{ label }} </h2>
        <div v-if="sessions.length">
            <div id="session-list-wrapper">
                <table id="session-list" @click.stop="sessionSelected" v-click-outside="sessionDeselected">
                    <thead>
                        <tr>
                            <th><h3>Subject</h3></th>
                            <th><h3>Session</h3></th>
                        </tr>
                    </thead>
                    <tbody>
                        <SessionListItem
                        v-for="session in sessions"
                        :key="session.id"
                        :session="session"
                        :isSelected="selectedSessionId == session.id || selectedAnalysisParentId == session.id"
                        />
                    </tbody>
                </table>
            </div>
            <div id="analysis-list-title">
                <h3>Analysis Outputs</h3>
            </div>
            <div id="analysis-list" @click.stop="analysisSelected">
                <AnalysisListItem
                v-for="(analysis, index) in analyses"
                :key="index"
                :analysis="analysis"
                :hide="selectedSessionId != '' && selectedSessionId != analysis.parent"
                @file-clicked="onFileClicked"
                />
            </div>
            <br clear="all"/>
            <router-link class="taglink" :to="{ name: 'tag', params: { projectId: id, projectLabel: label, selectedFiles: selectedFiles }}">Next >></router-link>
        </div>
        <div v-else>
            {{ status }}
        </div>
    </div>
</template>

<script>
import { Flywheel } from '../../services/Flywheel'
import AnalysisListItem from './AnalysisListItem'
import SessionListItem from './SessionListItem'

let fw

export default {
    components: { AnalysisListItem, SessionListItem },
    props: {
        id: {
            type: String,
            required: true
        }
    },
    data() {
        return { 
            label: '',
            sessions: [],
            analyses: [],
            selectedAnalysisParentId: '',
            selectedFiles: [],
            selectedSessionId: '',
            status: 'Loading sessions...'
        }
    },
    created() {
        fw = new Flywheel(sessionStorage.fwApiKey, process.env.VUE_APP_FW_URL)
        fw.getProject(this.id).then(res => {
            this.label = res['label']
            if (res['analyses'].length > 0) {
                this.sessions = res['sessions']
                this.analyses = res['analyses']
            } else {
                this.status = `No analyses found for ${res['label']}`
            }
        }).catch(err => {
            this.status = 'Whoops! We hit an error trying to load the analyses. Please reload the page to try again.'
            console.log(err)
        })
    },
    methods: {
        analysisSelected: function(event) {
            // clicks on a label also generate a click on the corresponding
            // input, so we'll ignore label clicks
            if (event.target.tagName !== 'LABEL') {
                const analysisNode = event.target.closest('.analysis')
                this.selectedAnalysisParentId = analysisNode.dataset.sessid
            }
        },
        onFileClicked: function(fileClickEvent) {
            if (fileClickEvent.selected) {
                this.selectedFiles.push(fileClickEvent.file)
            } else {
                const idx = this.selectedFiles.findIndex(function(elem) {
                    return elem.analysisId === this.analysisId && elem.name == this.name
                }, fileClickEvent.file)
                if (idx != -1) {
                    this.selectedFiles.splice(idx, 1)
                }
            }
        },
        sessionDeselected: function() {
            this.selectedSessionId = ''
            this.selectedAnalysisParentId = ''
        },
        sessionSelected: function(event) {
            if (event.target.tagName == 'TD') {
                this.selectedSessionId = event.target.parentNode.dataset.sessid
                this.selectedAnalysisParentId = ''
            }
        }
    }
}
</script>

<style>
    #session-list-wrapper {
        width: 40%;
        float: left;
        max-height: 532px;
        overflow-y: scroll;
        border-bottom: solid 1px lightgrey;
    }
    #session-list {
        border-collapse: collapse;
        width: 100%;
        cursor: pointer;
    }
    #session-list tr td {
        padding-right: 100px;
        text-align: center;
    }
    #session-list tr th {
        text-align: left;
    }
    .taglink {
        float: right;
        padding: 40px 40px 0px 0px;
        font-size: 16px;
        font-weight: bold;
    }
    th, td {
        border-bottom: 1px solid #ddd;
        padding: 10px;
    }
    #analysis-list-title, #analysis-list {
        margin-left: 40px;
        float:left;
        width: 55%;
    }
    #analysis-list {
        height: 450px;
        overflow: scroll;
        border-bottom: 1px solid lightgray;
        padding: 10px;
    }
</style>