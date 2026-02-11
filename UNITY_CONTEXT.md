# UNITY_CONTEXT.md

This file provides Unity ERP business context for Claude Code when working with any app in this repository.

## Unity ERP Overview

Unity ERP is a comprehensive educational institution management system serving schools with complete student lifecycle management, from lead generation through alumni tracking. Built on the Frappe framework, Unity addresses the unique challenges of educational institutions with specialized workflows, compliance requirements, and multi-stakeholder environments.

## Core Business Architecture

### Educational Institution Complexities

Educational institutions operate fundamentally differently from businesses:
- **Academic Calendar Driven**: All operations align with academic years, terms, and sessions
- **Multi-Stakeholder Environment**: Students, parents, teachers, administration, and regulatory bodies
- **Lifecycle-Based Operations**: Students progress through predictable stages requiring different services
- **Compliance Heavy**: RTE, CBSE, state education boards, child protection regulations
- **Relationship-Centric**: Long-term relationships spanning multiple years and family members

### Student Lifecycle Flow

**Lead Generation → Student Applicant → Student → Program Enrollment → Alumni**

1. **Lead Management**: Marketing and inquiry tracking through multiple channels
2. **Admission Process**: Application, document verification, assessment, selection
3. **Student Onboarding**: Enrollment, fee structure assignment, account creation
4. **Academic Journey**: Curriculum delivery, assessment, progress tracking
5. **Graduation/Transfer**: Certification, alumni management, record preservation

## Educational Domain Modules

### 1. Student Lifecycle Management

#### CRM & Lead Management
- **WhatsApp Bot Integration**: Automated lead qualification and information gathering
- **Visual Workflow Builder**: Customizable funnel management for different admission streams
- **Multi-Channel Tracking**: Website, social media, referrals, walk-ins
- **Lead Scoring**: Qualification based on admission probability and fit

#### Admissions Module
- **Document Management**: Birth certificates, previous school records, medical certificates
- **Assessment Integration**: Entrance tests, interviews, portfolio reviews
- **Capacity Management**: Class-wise seat allocation and waiting list management
- **Regulatory Compliance**: Age verification, domicile requirements, quota management

#### Student Management
- **Comprehensive Profiles**: Academic, health, behavioral, family information
- **Multi-Entity Support**: Students transferring between branches/schools
- **Status Management**: Academic (enrolled, promoted, detained), Financial (current, defaulter), Behavioral (good standing, disciplinary)
- **Lifecycle Tracking**: Complete journey from inquiry to alumni

### 2. Academic Delivery

#### Curriculum Map™
- **Standards Alignment**: State boards, CBSE, ICSE, international curricula
- **Scope and Sequence**: Chapter-wise, unit-wise planning with timing
- **Teacher Assignment**: Subject expertise mapping and workload distribution
- **Resource Management**: Textbooks, supplementary materials, digital resources

#### Learning Management System (LMS)
- **Content Delivery**: Video lessons, interactive content, assignments
- **Assessment Tools**: Quizzes, assignments, projects, presentations
- **Progress Tracking**: Learning analytics, engagement metrics, intervention triggers
- **Parent Visibility**: Home learning support, progress monitoring

#### Assessment & Examination
- **Multiple Methodologies**: Formative, summative, portfolio, project-based
- **Age-Appropriate Tools**: Play-based for kindergarten, competitive for seniors
- **Grading Systems**: Marks, grades, descriptive feedback, skill-based assessment
- **Report Cards**: Comprehensive academic and behavioral reporting

### 3. Financial Management

#### Fee Management
- **Complex Structures**: Academic fees, transport, meals, activities, deposits
- **Multi-Entity Splitting**: Trust fees, school fees, transport vendor fees
- **Scholarship Integration**: Merit-based, need-based, government schemes
- **Payment Flexibility**: Installments, advance payments, emergency assistance

#### Accounting Integration
- **Educational Accounting**: Different from business accounting (fund accounting)
- **Regulatory Reporting**: Trust requirements, audit compliance, tax obligations
- **Budget Management**: Academic year budgeting, capital expenditure planning

### 4. Human Resources

#### Educational HR Specialization
- **Academic Roles**: Teachers, coordinators, principals, counselors
- **Certification Tracking**: Teaching licenses, subject expertise, continuing education
- **Performance Management**: Academic delivery, student outcomes, parent satisfaction
- **Specialized Payroll**: Academic calendar alignment, summer break management

### 5. Communication & Engagement

#### Multi-Channel Communication
- **WhatsApp Business**: Parent-teacher communication, notices, emergency alerts
- **Mobile Apps**: Parent portal, student portal, teacher tools
- **Traditional Channels**: Email, SMS, phone calls, physical notices
- **Emergency Communication**: Crisis management, immediate alerts

#### Parent Engagement
- **Progress Sharing**: Academic updates, behavioral reports, achievement celebrations
- **Participation Opportunities**: Events, volunteer activities, feedback sessions
- **Digital Access**: Anytime access to student information, school updates

## Integration Architecture

### External Integrations

#### Google Workspace for Education
- **Account Management**: Automated student and staff account provisioning
- **Classroom Integration**: Google Classroom, Drive, Meet for virtual learning
- **Calendar Synchronization**: Academic calendar, events, parent-teacher meetings
- **Document Collaboration**: Shared resources, collaborative projects

#### Payment Gateway Diversity
- **Multiple Options**: Different gateways for different fee types and amounts
- **Payment Splitting**: Automatic distribution to different entities/accounts
- **Reconciliation**: Automated matching with fee records and accounting entries
- **Parent Convenience**: Saved payment methods, installment automation

#### Communication Platforms
- **WhatsApp Business API**: Rich messaging, media sharing, automated responses
- **SMS Integration**: Backup communication, delivery confirmations
- **Email Systems**: Professional communication, document attachments

### Frontend Architecture

#### Multi-Portal System
- **Parent Portal (Walsh)**: Student information, fee payments, communication
- **Administrative Portal (WalnutMGR)**: Data management, reporting, configuration
- **UI Component Library**: Consistent user experience across all interfaces

#### Mobile-First Design
- **Parent App**: Primary interface for most parent interactions
- **Offline Capability**: Essential features work without internet
- **Push Notifications**: Real-time updates and emergency communications

## Key Business Workflows

### Cross-Module Workflows

#### Student Admission Process
1. **Lead Capture** (CRM) → **Application** (Admissions) → **Assessment** (Academics)
2. **Selection** (Admissions) → **Enrollment** (Student Management) → **Fee Assignment** (Fees)
3. **Account Creation** (Google Integration) → **Parent Onboarding** (Communication)

#### Academic Rollover (Year-End Processing)
1. **Academic Results** (Assessment) → **Promotion Decision** (Student Management)
2. **Class Assignment** (Student Management) → **Fee Structure Update** (Fees)
3. **Timetable Generation** (Academics) → **Teacher Assignment** (HR)

#### Fee Collection Cycle
1. **Fee Generation** (Fees) → **Payment Reminders** (Communication)
2. **Payment Processing** (Payment Gateways) → **Receipt Generation** (Accounting)
3. **Defaulter Management** (Fees) → **Access Control** (Student Management)

### Multi-Entity Operations

#### Shared Services
- **Centralized Admissions**: Multiple schools using common admission process
- **Staff Mobility**: Teachers working across multiple entities
- **Resource Sharing**: Curriculum, training materials, best practices
- **Consolidated Reporting**: Chain-level analytics and compliance

#### Entity-Specific Operations
- **Local Compliance**: State-specific requirements, local regulations
- **Cultural Adaptation**: Regional festivals, local language support
- **Fee Structures**: Economic conditions, local competition

## Educational Domain Considerations

### Regulatory Compliance

#### Right to Education (RTE) Act
- **Free Education**: Automated fee exemption for eligible students
- **Admission Quotas**: 25% reservation tracking and management
- **Age Requirements**: Automatic age verification and appropriate class placement
- **Documentation**: Compliance reporting and audit trails

#### Board Requirements (CBSE, State Boards)
- **Student Records**: Comprehensive academic and personal information
- **Assessment Standards**: Board-specific grading and evaluation methods
- **Teacher Qualifications**: Certification and experience tracking
- **Infrastructure Compliance**: Facility and resource requirements

### Data Protection & Privacy

#### Minor Data Protection
- **Parent Consent**: All data collection requires guardian approval
- **Limited Access**: Role-based access with minimal necessary information
- **Data Retention**: Educational record retention as per regulations
- **Anonymization**: Research and analytics with protected identities

#### Stakeholder Privacy
- **Staff Information**: Professional boundaries and privacy protection
- **Family Information**: Confidential family circumstances and challenges
- **Academic Records**: Protection of academic performance and behavioral records

## Development Patterns

### Educational Domain Patterns

#### Student-Centric Design
- **Single Student View**: All information accessible from student profile
- **Family Relationships**: Sibling connections, guardian relationships
- **Historical Tracking**: Complete academic journey preservation
- **Future Planning**: Academic pathway and career guidance integration

#### Academic Calendar Integration
- **Time-Bounded Operations**: All processes respect academic calendar
- **Seasonal Workflows**: Different processes for admission season, examination period
- **Holiday Awareness**: No critical operations during student holidays
- **Year-End Processing**: Comprehensive rollover and preparation procedures

#### Multi-Stakeholder Experience
- **Role-Based Interfaces**: Different experiences for parents, teachers, administrators
- **Communication Preferences**: Stakeholder-specific channels and timing
- **Access Controls**: Information sharing based on relationships and permissions
- **Feedback Loops**: Continuous improvement based on stakeholder input

### Technical Architecture Patterns

#### Multi-Entity Data Isolation
- **Tenant Separation**: Complete data isolation between entities
- **Shared Services**: Common functionality with entity-specific configuration
- **Cross-Entity Operations**: Controlled data sharing for transfers and shared services

#### Educational Workflow Automation
- **Lifecycle Triggers**: Automatic processes based on student lifecycle events
- **Compliance Automation**: Regulatory requirement fulfillment without manual intervention
- **Communication Automation**: Proactive stakeholder communication

#### Integration Resilience
- **Graceful Degradation**: Essential functions continue during integration failures
- **Data Synchronization**: Eventual consistency with immediate local operations
- **Audit Trails**: Complete operational history for compliance and troubleshooting

## Security & Compliance Framework

### Access Control
- **Principle of Least Privilege**: Minimum necessary access for role fulfillment
- **Time-Based Access**: Academic year and term-based permissions
- **Relationship-Based Access**: Parent access to their children's information only
- **Professional Boundaries**: Teacher access limited to their students and subjects

### Audit & Compliance
- **Complete Audit Trails**: All operations logged with user, time, and purpose
- **Regulatory Reporting**: Automated generation of compliance reports
- **Data Integrity**: Checksums and validation for critical educational records
- **Emergency Procedures**: Crisis management and data protection protocols

## Performance & Scale Considerations

### Educational Institution Scale
- **Student Population**: 500-5000 students per entity
- **Staff Size**: 50-500 employees depending on institution size
- **Parent Engagement**: High interaction during specific periods (admission, results, events)
- **Seasonal Load**: Peak usage during admission season, examination periods

### Performance Patterns
- **Academic Calendar Peaks**: Admission season, result declaration, fee collection
- **Daily Patterns**: Morning attendance, afternoon parent communication, evening homework
- **Communication Bursts**: Emergency notifications, result announcements, event reminders

This comprehensive business context provides the foundation for understanding Unity ERP's educational domain focus and architectural decisions. All technical implementations should consider these business requirements and stakeholder needs.