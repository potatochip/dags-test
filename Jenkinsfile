pipeline {
    options {
        parallelsAlwaysFailFast()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        COMPOSE_DOCKER_CLI_BUILD = 1
        PROJECT = 'dags'
        CHANNEL = '#data-notifications'
        IMAGE = "juvo/${PROJECT}"
        REGISTRY = "registry.juvo.mobi"
        DOCKER_RUN = "docker-compose exec -T ci"
    }

    agent {
        kubernetes {
            label 'jenkins-data'
            yaml libraryResource('pod_templates/data_agent_dind.yaml')
            defaultContainer 'jenkins-agent-data'
            // idleMinutes 600
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
                        sh "docker pull ${REGISTRY}/${IMAGE}:latest || true"
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
            when {
                not {
                    branch "master"
                }
            }
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", "juvo-registry-credentials") {
                        sh "docker tag ${IMAGE} ${REGISTRY}/${IMAGE}:latest"
                        sh "docker tag ${IMAGE} ${REGISTRY}/${IMAGE}:${CHANGE_BRANCH} || true"
                        sh "docker push ${REGISTRY}/${IMAGE}"
                    }
                }
            }
        }
        stage('Run Tests') {
            parallel {
                stage('Type Check Packages') {
                    steps {
                        sh "ls -la"
                        sh "ls -la dag"
                        sh "${DOCKER_RUN} mypy -p dag --junit-xml reports/mypy_dag.xml"
                        sh "${DOCKER_RUN} mypy -p utils --junit-xml reports/mypy_utils.xml"
                    }
                }
                stage('Type Check Dags') {
                    steps {
                        sh "${DOCKER_RUN} mypy --namespace-packages -p dags --junit-xml reports/mypy_dags.xml"
                    }
                }
                stage('Type Check Plugins') {
                    steps {
                        sh "${DOCKER_RUN} mypy --namespace-packages -p plugins --junit-xml reports/mypy_plugins.xml"
                    }
                }
                stage('Test') {
                    steps {
                        sh "${DOCKER_RUN} pytest --junitxml=reports/nosetests.xml --cov --cov-report=xml:reports/coverage.xml --cov-report=html:reports/coverage.html"
                    }
                }
            }
        }
        stage('Static Analysis') {
            steps {
                sh 'docker cp "$(docker-compose ps -q ci)":/srv/reports .'
                sh "sed -i 's|/srv|${WORKSPACE}|' reports/coverage.xml"
                withSonarQubeEnv('SonarQube') {
                    sh "sonar-scanner -Dsonar.host.url=${SONAR_HOST_URL} -Dsonar.projectKey=${PROJECT}  -Dsonar.python.coverage.reportPaths=reports/coverage.xml"
                }
            }
        }
        stage('Build Prod Image') {
            when {
                branch "master"
            }
            steps {
                sh "docker build -t ${IMAGE}:${TAG} --target production -f docker/airflow/Dockerfile \\."
            }
        }
        stage('Push Prod Image') {
            when {
                branch "master"
            }
            steps {
                pushDockerContainer(env.IMAGE, env.TAG)
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
