pipeline {
    options {
        parallelsAlwaysFailFast()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PROJECT = 'dags'
        CHANNEL = '#test-slack-notif'
        IMAGE = "juvo/${PROJECT}"
        TEST_CONTAINER = "${PROJECT}_test"
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
        stage('Build Test Container') {
            steps {
                sh "docker build --target test -t ${IMAGE} -f docker/airflow/Dockerfile \\."
                sh "docker run --name ${TEST_CONTAINER} -v ${WORKSPACE}:/srv -it -d ${IMAGE}"
                sh "docker exec ${TEST_CONTAINER} airflow initdb"
            }
        }
        stage('Test') {
            parallel {
                stage('Type Check Packages') {
                    steps {
                        sh "docker exec ${TEST_CONTAINER} mypy -p dag --junit-xml reports/mypy_packages.xml"
                    }
                }
                stage('Type Check Dags') {
                    steps {
                        sh "docker exec ${TEST_CONTAINER} mypy --namespace-packages -p dags --junit-xml reports/mypy_dags.xml"
                    }
                }
                stage('Type Check Plugins') {
                    steps {
                        sh "docker exec ${TEST_CONTAINER} mypy --namespace-packages -p plugins --junit-xml reports/mypy_plugins.xml"
                    }
                }
                stage('Test') {
                    steps {
                        sh "docker exec ${TEST_CONTAINER} pytest --junitxml=reports/nosetests.xml --cov --cov-report=xml:reports/coverage.xml --cov-report=html:reports/coverage.html"
                    }
                }
            }
        }
       stage('Static Analysis') {
            steps {
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
        stage('Push') {
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
            sh "docker rm --force ${TEST_CONTAINER}"
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
