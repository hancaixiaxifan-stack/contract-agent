import { createRouter, createWebHistory } from "vue-router"
import HomePage from "../pages/HomePage.vue"
import TextUploadPage from "../pages/TextUploadPage.vue"
import PdfUploadPage from "../pages/PdfUploadPage.vue"
import ResultPage from "../pages/ResultPage.vue"
import ResultDetailPage from "../pages/ResultDetailPage.vue"
import HistoryPage from "../pages/HistoryPage.vue"
import HistoryDetailPage from "../pages/HistoryDetailPage.vue"

const routes = [
  {
    path: "/",
    name: "Home",
    component: HomePage
  },
  {
    path: "/upload/text",
    name: "TextUpload",
    component: TextUploadPage
  },
  {
    path: "/upload/pdf",
    name: "PdfUpload",
    component: PdfUploadPage
  },
  {
    path: "/result",
    name: "Result",
    component: ResultPage
  },
  {
    path: "/result-detail",
    name: "ResultDetail",
    component: ResultDetailPage
  },
  {
    path: "/history",
    name: "History",
    component: HistoryPage
  },
  {
    path: "/history-detail",
    name: "HistoryDetail",
    component: HistoryDetailPage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router