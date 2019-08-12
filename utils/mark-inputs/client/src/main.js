import Vue from 'vue'
import App from './App.vue'
import VueRouter from 'vue-router'

import ApiKey from './components/ApiKey'
import ProjectPage from './components/ProjectPage'
import ProjectList from './components/ProjectList'
import Tag from './components/Tag'
import Upload from './components/Upload'

Vue.use(VueRouter)

function getApiKeyForProps() {
  return { fwApiKey: sessionStorage.fwApiKey }
}

const routes =
[
  { path: '/', component: ApiKey }, 
  { 
    path: '/projects',
    component: ProjectList,
    props: getApiKeyForProps
  },
  {
    name: 'project',
    path: '/project/:id',
    component: ProjectPage,
    props: true
  },
  { name: 'tag',
    path: '/tag',
    component: Tag,
    props: true
  },
  {
    name: 'upload',
    path: '/upload',
    component: Upload,
    props: true
  }
]
const router = new VueRouter({
  routes: routes,
  mode: 'history'
})


Vue.config.productionTip = false

// see https://stackoverflow.com/questions/36170425/detect-click-outside-element/36180348
// and https://vuejs.org/v2/guide/custom-directive.html#Directive-Hook-Arguments
Vue.directive('click-outside', {
  bind: function (el, binding, vnode) {
    el.clickOutsideEvent = function (event) {
      // here I check that click was outside the el and his childrens
      if (el != event.target) {
        // and if it did, call method provided in attribute value
        vnode.context[binding.expression](event);
      }
    };
    document.body.addEventListener('click', el.clickOutsideEvent)
  },
  unbind: function (el) {
    document.body.removeEventListener('click', el.clickOutsideEvent)
  },
});

new Vue({
  render: h => h(App),
  router
}).$mount('#app')
