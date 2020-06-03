pipeline {
    options {
        parallelsAlwaysFailFast()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        COMPOSE_DOCKER_CLI_BUILD = 1
        PROJECT = 'dags'
        CHANNEL = '#data-notifications'
        REGISTRY = "registry.juvo.mobi"
        IMAGE = "juvo/${PROJECT}"
        CACHE_IMAGE = "${REGISTRY}/${IMAGE}:latest"
        DOCKER_RUN = "docker-compose exec -T ci"
    }

    agent {
        kubernetes {
            label 'jenkins-data'
            yaml libraryResource('pod_templates/data_agent_dind.yaml')
            defaultContainer 'jenkins-agent-data'
            idleMinutes 600
        }
    }

    stages {
        stage('Start') {
            steps {
                sendStartBuildNotification(env.CHANNEL)
                cleanWs()
                checkout scm
                script {
                    env.HASH = getGitCommitHash()
                    env.TAG = buildDockerTag(env.BRANCH_NAME, env.HASH)
                }
            }
        }
        stage('Lint') {
            steps {
                sh "flake8 ."
            }
        }
        stage('Pull Cache') {
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", "juvo-registry-credentials") {
                        sh "docker pull ${CACHE_IMAGE} || true"
                    }
                }
            }
        }
        stage('Build Test Container') {
            steps {
                sh "docker-compose build ci"
                sh "docker-compose up -d ci"
            }
        }
        stage('Cache Image') {
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", "juvo-registry-credentials") {
                        sh "docker push ${CACHE_IMAGE}"
                    }
                }
            }
        }
        stage('Run Tests') {
            parallel {
                stage('Type Check Packages') {
                    steps {
                        sh "${DOCKER_RUN} mypy -p dag --junit-xml reports/mypy_dag.xml"
                    }
                }
                stage('Type Check Dags') {
                    steps {
                        sh "${DOCKER_RUN} mypy dags/*/* --junit-xml reports/mypy_dags.xml"
                    }
                }
                stage('Type Check Plugins') {
                    steps {
                        sh "${DOCKER_RUN} mypy -p plugins --junit-xml reports/mypy_plugins.xml"
                    }
                }
                stage('Test') {
                    steps {
                        sh "${DOCKER_RUN} pytest -v --junitxml=reports/nosetests.xml --cov --cov-report=xml:reports/coverage.xml --cov-report=html:reports/coverage.html"
                    }
                }
            }
        }
        stage('Static Analysis') {
            when {
                branch "master"
            }
            steps {
                sh 'docker cp "$(docker-compose ps -q ci)":/srv/reports .'
                sh "sed -i 's|/srv|${WORKSPACE}|' reports/coverage.xml"
                withSonarQubeEnv('SonarQube') {
                    sh "sonar-scanner -Dsonar.host.url=${SONAR_HOST_URL} -Dsonar.projectKey=${PROJECT} -Dsonar.sources=dag,dags,plugins -Dsonar.python.coverage.reportPaths=reports/coverage.xml"
                }
            }
        }
    }

    post {
        always {
            sh 'docker cp "$(docker-compose ps -q ci)":/srv/reports .'
            sh "docker-compose down --remove-orphans -t 0"
            archiveArtifacts artifacts: 'reports/*', fingerprint: true
            junit 'reports/*.xml'
        }
        failure {
            sendEndBuildNotification(currentBuild.currentResult, env.CHANNEL, '')
        }
        success {
            sendEndBuildNotification(currentBuild.currentResult, env.CHANNEL, "Built docker image ${IMAGE}:${TAG}")
        }
    }
}
