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
                        <Session
                        v-for="session in sessions"
                        :key="session.id"
                        :session="session"
                        :isSelected="selectedSessionId == session.id"
                        />
                    </tbody>
                </table>
            </div>

            <div class="tab-nav">
                <button @click="onTabClicked" class="tab-btn">Acquisitions</button>
                <button @click="onTabClicked" class="selected tab-btn">Analysis Outputs</button>
            </div>

            <div v-if="displayAcquisitions.length" id="acquisition-list" class="hidden tab-contents" @click.stop="fileContainerSelected">
                <FileContainer
                v-for="(acquisition, index) in displayAcquisitions"
                :key="index"
                :fileContainer="acquisition"
                @file-clicked="onFileClicked"
                />
            </div>
            <div v-else id="acquisition-list" class="hidden tab-contents">
                <h4> {{ acqLoadingStatus }} </h4>
            </div>

            <div v-if="displayAnalyses.length" id="analysis-list" @click.stop="fileContainerSelected" class="tab-contents">
                <FileContainer
                v-for="(analysis, index) in displayAnalyses"
                :key="index"
                :fileContainer="analysis"
                @file-clicked="onFileClicked"
                />
            </div>
            <div v-else id="analysis-list" class="tab-contents">
                {{ analysisLoadingStatus }}
            </div>
            <br clear="all"/>
            <router-link class="taglink" :to="{ name: 'tag', params: { projectId: id, projectLabel: label, selectedFiles: selectedFiles }}">Next >></router-link>
        </div>
        <div v-else>
            {{ sessionLoadingStatus }}
        </div>
    </div>
</template>

<script>
import { Flywheel } from '../../services/Flywheel'
import FileContainer from './FileContainer'
import Session from './Session'
import TagManager from '../../services/TagManager'

let fw

export default {
    components: { FileContainer, Session, TagManager },
    props: {
        id: {
            type: String,
            required: true
        }
    },
    computed: {
        acqLoadingStatus() {
            if (!this.selectedSessionId) {
                return 'Select a session to load acquisitions for that session.'
            } else {
                const sess = this.sessions.find(el => el.id == this.selectedSessionId)
                if (sess.acqLoadingStatus == 'loading') {

                } else if (sess.acqLoadingStatus == 'loaded') {
                    return `No acquisitions found for subject ${sess.subject_label}, session ${sess.label}`
                } else {
                    return 'An error occurred loading the acquisitions for this session. Please click it again.'
                }
            }
        },
        displayAcquisitions() {
            if (this.sessionIsSelected) {
                const selectedSess = this.sessions.find(el => el.id == this.selectedSessionId)
                return selectedSess.acquisitions
            }

            return this.sessions.flatMap(s => s.acquisitions)
        },
        displayAnalyses() {
            if (this.sessionIsSelected) {
                const selectedSess = this.sessions.find(el => el.id == this.selectedSessionId)
                return selectedSess.analyses
            }

            return this.sessions.flatMap(s => s.analyses)
        }
    },
    data() {
        return { 
            label: '',
            sessions: [],
            sessionIsSelected: false, // true when a user clicks on a session
            selectedFiles: [],
            selectedSessionId: '', // set when user clicks on session OR on analysis OR on acquisition
            sessionLoadingStatus: 'Loading sessions...',
            analysisLoadingStatus: 'Loading analyses...'
        }
    },
    created() {
        // put files that don't have a tag into selectedFiles
        this.selectedFiles = TagManager.getAllTags().filter(t => !t.tag).flatMap(t => t.files)

        fw = new Flywheel(sessionStorage.fwApiKey, process.env.VUE_APP_FW_URL)
        fw.getSessionsForProject(this.id).then(res => {
            this.label = res.project_label
            if (res.sessions.length > 0) {
                this.sessions = res.sessions.map(s => {
                    s.acqLoadingStatus = 'unloaded'
                    return s
                })
                return fw.getAnalysesForProject(this.id)
            } else {
                this.sessionLoadingStatus = 'No sessions found for this project.'
                return []
            }
        })
        .then((analyses) => {
            // set this regardless of whether or not analyses were found
            // it will be displayed if the user clicks on a session that
            // has no analyses, or if there are no analyses for the entire project.
            this.analysisLoadingStatus = 'No analyses found.'

            analyses.forEach(a => {
                a.parentType = 'analysis'
                a.files.forEach(f => {
                    f.isSelected = this.fileIsSelected(a.id, f.name)
                })
                const aSessId = a.parent
                const sessIdx = this.sessions.findIndex(el => el.id == aSessId)
                this.sessions[sessIdx].analyses.push(a)
            })
        })
        .catch(err => {
            this.sessionLoadingtatus = 'Whoops! We hit an error trying to load the sessions. Please reload the page to try again.'
            console.log(err)
        })
    },
    methods: {
        acquisitionTabSelected: function() {
            // TODO use $refs instead of document.getElement
            return !document.getElementById('acquisition-list').classList.contains('hidden')
        },
        fileContainerSelected: function(event) {
            // Triggered either when clicking on anything in the acqusitions or analyses tab.
            // Clicks on a label also generate a click on the corresponding
            // input, so we'll ignore label clicks.
            if (event.target.tagName !== 'LABEL') {
                const acquisitionNode = event.target.closest('.file-container')
                this.selectedSessionId = acquisitionNode.dataset.sessid
            }
        },
        fileIsSelected: function(fileParentId, fileName) {
            return this.selectedFiles.findIndex(el => el.parentId == fileParentId && el.name == fileName) != -1
        },
        loadAcquisitionsForSession: function(sessId) {
            const sess = this.sessions.find(el => el.id == sessId)
            if (sess.acqLoadingStatus == 'unloaded' || sess.acqLoadingStatus == 'error') {
                sess.acqLoadingStatus = 'loading'
                fw.getAcquisitionsForSession(sessId)
                .then(acqs => {
                    sess.acqLoadingStatus = 'loaded'
                    sess.acquisitions = acqs.map(a => {
                        a.parentType = 'acquisition'
                        a.files.forEach(f => {
                            f.isSelected = this.fileIsSelected(a.id, f.name)
                        })
                        return a
                    })
                })
                .catch(err => {
                    sess.acqLoadingStatus = 'error'
                    console.log(err);
                })
            }
        },
        onFileClicked: function(fileClickEvent) {
            if (fileClickEvent.selected) {
                this.selectedFiles.push(fileClickEvent.file)
            } else {
                const deselectedItemParentId = fileClickEvent.file.parentId
                const deselectedItemName = fileClickEvent.file.name
                const idx = this.selectedFiles.findIndex(function(elem) {
                    return elem.parentId == deselectedItemParentId && elem.name == deselectedItemName
                })
                if (idx != -1) {
                    this.selectedFiles.splice(idx, 1)
                }
            }
        },
        sessionDeselected: function() {
            this.selectedSessionId = ''
            this.sessionIsSelected = false
        },
        sessionSelected: function(event) {
            if (event.target.tagName == 'TD') {
                this.selectedSessionId = event.target.parentNode.dataset.sessid
                this.sessionIsSelected = true
                if (this.acquisitionTabSelected()) {
                    this.loadAcquisitionsForSession(event.target.parentNode.dataset.sessid)
                }
            }
        },
        onTabClicked: function(event) {
            // TODO use $refs instead of document.getElement
            const tabBtns = document.getElementsByClassName('tab-btn')
            for (var btn of tabBtns) {
                btn.classList.toggle("selected")
            }

            document.getElementById('acquisition-list').classList.toggle('hidden')
            document.getElementById('analysis-list').classList.toggle('hidden')
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
    .tab-nav {
        float: left;
        margin: 10px 0 0 50px;
    }
    .tab-btn {
        padding: 15px 50px 15px 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        background-color: rgb(182, 177, 177);
        color: white;
        border-radius: 10px 10px 0 0;
        outline: none;
    }
    .tab-btn.selected {
        background-color: white;
        color: black;
        border-bottom: none;
    }
    .tab-btn:not(:focus):hover {
        background-color: rgb(94, 92, 92);
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
    #acquisition-list-title {
        float: left;
        width: 20%;
    }
    .tab-contents {
        height: 450px;
        overflow: scroll;
        border-bottom: 1px solid lightgray;
        padding: 10px;
        margin-left: 40px;
        float:left;
        width: 40%;
    }
</style>