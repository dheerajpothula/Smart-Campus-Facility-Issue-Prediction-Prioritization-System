import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { taxonomyService } from '../../services/taxonomyService';
import { complaintService } from '../../services/complaintService';
import { uploadService } from '../../services/uploadService';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Textarea } from '../../components/ui/Textarea';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Notification } from '../../components/ui/Notification';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type { TaxonomyHierarchyResponse, StudentComplaintCreatePayload } from '../../types';
import {
  Send,
  Upload,
  CheckCircle2,
  FileText,
  Calendar,
  Clock,
  MapPin,
  Phone,
  Image as ImageIcon,
  Check,
  ShieldAlert,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';

const APPROVED_TIME_SLOTS = [
  '08:00–10:00',
  '10:00–12:00',
  '12:00–14:00',
  '14:00–16:00',
  '16:00–18:00',
];

export const RaiseQueryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Agreement Session State (must agree once per session to unlock form)
  const [isAgreed, setIsAgreed] = useState<boolean>(() => {
    return sessionStorage.getItem('fipp_student_agreed') === 'true';
  });

  // Agreement checkboxes
  const [decResponsible, setDecResponsible] = useState<boolean>(false);
  const [decDisciplinary, setDecDisciplinary] = useState<boolean>(false);
  const [decTruthful, setDecTruthful] = useState<boolean>(false);

  // Taxonomy state
  const [taxonomy, setTaxonomy] = useState<TaxonomyHierarchyResponse | null>(null);
  const [loadingTaxonomy, setLoadingTaxonomy] = useState<boolean>(true);

  // Form states with draft restoration
  const savedDraft = useMemo(() => {
    try {
      const raw = sessionStorage.getItem('fipp_query_draft');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }, []);

  const [messageType, setMessageType] = useState<string>(savedDraft?.messageType || 'Grievance');
  const [title, setTitle] = useState<string>(savedDraft?.title || '');
  const [category, setCategory] = useState<string>(savedDraft?.category || '');
  const [subCategory, setSubCategory] = useState<string>(savedDraft?.subCategory || '');
  const [specificCategories, setSpecificCategories] = useState<string[]>(savedDraft?.specificCategories || []);
  const [building, setBuilding] = useState<string>(savedDraft?.building || '');
  const [subBlock, setSubBlock] = useState<string>(savedDraft?.subBlock || '');
  const [roomType, setRoomType] = useState<string>(savedDraft?.roomType || 'Room No');
  const [roomNumber, setRoomNumber] = useState<string>(savedDraft?.roomNumber || '');
  const [specifiedLocation, setSpecifiedLocation] = useState<string>(savedDraft?.specifiedLocation || '');
  const [contactNumber, setContactNumber] = useState<string>(savedDraft?.contactNumber || '');
  const [availabilityDate, setAvailabilityDate] = useState<string>(() => {
    if (savedDraft?.availabilityDate) return savedDraft.availabilityDate;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [timeSlot, setTimeSlot] = useState<string>(savedDraft?.timeSlot || APPROVED_TIME_SLOTS[0]);
  const [description, setDescription] = useState<string>(savedDraft?.description || '');

  // Attachment states
  const [uploadingPhoto, setUploadingPhoto] = useState<boolean>(false);
  const [uploadedPhotoName, setUploadedPhotoName] = useState<string | null>(savedDraft?.uploadedPhotoName || null);
  const [uploadedPhotoFilename, setUploadedPhotoFilename] = useState<string | null>(savedDraft?.uploadedPhotoFilename || null);
  const [uploadedPhotoSha256, setUploadedPhotoSha256] = useState<string | null>(savedDraft?.uploadedPhotoSha256 || null);

  // Submission & Alert states
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<{ token: string; message: string; category?: string } | null>(null);

  // Persist draft changes
  useEffect(() => {
    if (isAgreed && !successResult) {
      const draft = {
        messageType,
        title,
        category,
        subCategory,
        specificCategories,
        building,
        subBlock,
        roomType,
        roomNumber,
        specifiedLocation,
        contactNumber,
        availabilityDate,
        timeSlot,
        description,
        uploadedPhotoName,
        uploadedPhotoFilename,
        uploadedPhotoSha256,
      };
      sessionStorage.setItem('fipp_query_draft', JSON.stringify(draft));
    }
  }, [
    isAgreed,
    successResult,
    messageType,
    title,
    category,
    subCategory,
    specificCategories,
    building,
    subBlock,
    roomType,
    roomNumber,
    specifiedLocation,
    contactNumber,
    availabilityDate,
    timeSlot,
    description,
    uploadedPhotoName,
    uploadedPhotoFilename,
    uploadedPhotoSha256,
  ]);

  // Fetch taxonomy hierarchy on mount
  useEffect(() => {
    const fetchTaxonomy = async () => {
      try {
        const data = await taxonomyService.getHierarchy();
        setTaxonomy(data);

        // Pre-fill defaults if not restored from draft
        if (!savedDraft?.category && data.maintenance_categories?.length > 0) {
          setCategory(data.maintenance_categories[0]);
        }
        if (!savedDraft?.building && data.campus_blocks?.length > 0) {
          setBuilding(data.campus_blocks[0]);
        }
        if (!savedDraft?.timeSlot && data.time_slots?.length > 0) {
          setTimeSlot(data.time_slots[0]);
        }
      } catch (err: any) {
        setErrorMsg('Failed to load facility categories. Check backend connectivity.');
      } finally {
        setLoadingTaxonomy(false);
      }
    };
    fetchTaxonomy();
  }, [savedDraft]);

  // Cascading Category -> SubCategory reset
  const availableSubCategories = useMemo(() => {
    if (!taxonomy || !category) return [];
    const catMap = taxonomy.hierarchy?.[category];
    return catMap ? Object.keys(catMap) : [];
  }, [taxonomy, category]);

  // Handle Category Change (Resets Subcategory & Specific Categories)
  const handleCategoryChange = (newCat: string) => {
    setCategory(newCat);
    setSubCategory('');
    setSpecificCategories([]);
  };

  // Handle Message Type Change (Resets Category, Subcategory & Specific Categories)
  const handleMessageTypeChange = (newMsgType: string) => {
    setMessageType(newMsgType);
    setCategory('');
    setSubCategory('');
    setSpecificCategories([]);
  };

  // Handle SubCategory Change (Resets Specific Categories)
  const handleSubCategoryChange = (newSub: string) => {
    setSubCategory(newSub);
    setSpecificCategories([]);
  };

  // Available Specific Category checklist options
  const availableSpecificCategories: string[] = useMemo(() => {
    if (!taxonomy || !category || !subCategory) return [];
    const val: any = taxonomy.hierarchy?.[category]?.[subCategory];
    if (!val) return [];
    if (Array.isArray(val)) return val;
    if (typeof val === 'object') return Object.keys(val);
    return [];
  }, [taxonomy, category, subCategory]);

  const toggleSpecificCategory = (item: string) => {
    setSpecificCategories((prev) =>
      prev.includes(item) ? prev.filter((x) => x !== item) : [...prev, item]
    );
  };

  // Photo upload handler
  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingPhoto(true);
    setErrorMsg(null);
    try {
      const res = await uploadService.uploadPhoto(file);
      setUploadedPhotoName(file.name);
      setUploadedPhotoFilename(res.stored_filename);
      setUploadedPhotoSha256(res.sha256);
    } catch (err: any) {
      setErrorMsg(err.message || 'Photo upload validation failed.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  // Agreement Confirmation Handler
  const handleAgreeAndProceed = () => {
    if (decResponsible && decDisciplinary && decTruthful) {
      sessionStorage.setItem('fipp_student_agreed', 'true');
      setIsAgreed(true);
    }
  };

  // Complaint Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!isAgreed) {
      setErrorMsg('All mandatory declarations must be accepted before lodging a request.');
      return;
    }

    if (!category) {
      setErrorMsg('Please select a facility category.');
      return;
    }

    if (description.trim().length < 5) {
      setErrorMsg('Description must be at least 5 characters in length.');
      return;
    }

    if (description.trim().length > 500) {
      setErrorMsg('Description exceeds maximum limit of 500 characters.');
      return;
    }

    const cleanPhone = contactNumber.replace(/\D/g, '');
    if (cleanPhone.length !== 10 || !/^[6-9]\d{9}$/.test(cleanPhone)) {
      setErrorMsg('Please provide a valid 10-digit Indian mobile contact number (starting with 6-9).');
      return;
    }

    const payload: StudentComplaintCreatePayload = {
      category_type: 'Maintenance / Electrical Complaints',
      message_type: messageType,
      title: title.trim() || undefined,
      category,
      sub_category: subCategory || undefined,
      specific_categories: specificCategories,
      building,
      sub_block: subBlock || undefined,
      room_type: roomType,
      room_number: roomType === 'Room No' ? roomNumber : undefined,
      specified_location: roomType !== 'Room No' ? specifiedLocation : undefined,
      contact_number: cleanPhone,
      availability_date: availabilityDate,
      time_slot: timeSlot,
      description: description.trim(),
      declarations_accepted: true,
      photo_stored_filename: uploadedPhotoFilename || undefined,
      photo_sha256: uploadedPhotoSha256 || undefined,
    };

    setSubmitting(true);
    try {
      const result = await complaintService.submitStudentComplaint(payload);
      // Clear draft on successful submission
      sessionStorage.removeItem('fipp_query_draft');
      setSuccessResult({
        token: result.token,
        message: result.message,
        category: category,
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to register complaint. Please check your entries.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingTaxonomy) {
    return <LoadingSpinner label="Loading campus facility taxonomy..." className="py-20" />;
  }

  // -------------------------------------------------------------------------
  // STEP 1: MANDATORY AGREEMENT / UNDERTAKING SCREEN (IF NOT YET AGREED)
  // -------------------------------------------------------------------------
  if (!isAgreed) {
    const allAgreed = decResponsible && decDisciplinary && decTruthful;

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Raise a Facility Query</h1>
          <p className="text-xs text-[#52605B] mt-1">
            Student Facility Grievance Terms & Mandatory Undertaking
          </p>
        </div>

        <Card className="border-[#DCE5D8] shadow-sm">
          <CardHeader className="border-b border-[#DCE5D8]/60 bg-[#F5F7F2]/60 pb-4">
            <CardTitle className="text-sm flex items-center gap-2 text-[#172D28]">
              <ShieldAlert className="w-4 h-4 text-[#203A32]" /> Mandatory Declarations & Code of Conduct
            </CardTitle>
            <CardDescription>
              Please read and accept all three statutory undertakings to unlock the query submission form.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-5">
            <div className="space-y-4">
              <label className="flex items-start gap-3 p-3.5 rounded-lg border border-[#DCE5D8] bg-white hover:bg-[#F5F7F2]/40 transition-colors cursor-pointer">
                <input
                  type="checkbox"
                  checked={decResponsible}
                  onChange={(e) => setDecResponsible(e.target.checked)}
                  className="mt-0.5 rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
                />
                <span className="text-xs text-[#172D28] leading-relaxed">
                  <strong>1. Content Responsibility:</strong> I am responsible for the content typed in query.
                </span>
              </label>

              <label className="flex items-start gap-3 p-3.5 rounded-lg border border-[#DCE5D8] bg-white hover:bg-[#F5F7F2]/40 transition-colors cursor-pointer">
                <input
                  type="checkbox"
                  checked={decDisciplinary}
                  onChange={(e) => setDecDisciplinary(e.target.checked)}
                  className="mt-0.5 rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
                />
                <span className="text-xs text-[#172D28] leading-relaxed">
                  <strong>2. Disciplinary Undertaking:</strong> I understand that necessary disciplinary action can be initiated against me in case of use of derogatory words or false statements against any Student/Faculty/Staff/Higher Authority.
                </span>
              </label>

              <label className="flex items-start gap-3 p-3.5 rounded-lg border border-[#DCE5D8] bg-white hover:bg-[#F5F7F2]/40 transition-colors cursor-pointer">
                <input
                  type="checkbox"
                  checked={decTruthful}
                  onChange={(e) => setDecTruthful(e.target.checked)}
                  className="mt-0.5 rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
                />
                <span className="text-xs text-[#172D28] leading-relaxed">
                  <strong>3. Truthfulness Declaration:</strong> The information given by me regarding the complaint/request is true to the best of my knowledge and if found false/ wrong, necessary disciplinary action can be initiated against me.
                </span>
              </label>
            </div>

            <div className="pt-2">
              <Button
                variant="primary"
                size="lg"
                className="w-full justify-center"
                disabled={!allAgreed}
                onClick={handleAgreeAndProceed}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Agree & Proceed to Form
              </Button>
              {!allAgreed && (
                <p className="text-center text-[11px] text-[#52605B] mt-2">
                  Please select all 3 checkboxes above to enable the Agree &amp; Proceed button.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // STEP 2: SUBMISSION SUCCESS SCREEN (KEEPS STUDENT IN RAISE QUERY)
  // -------------------------------------------------------------------------
  if (successResult) {
    return (
      <Card className="max-w-2xl mx-auto shadow-md border-emerald-200">
        <CardContent className="p-8 text-center space-y-5">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-9 h-9" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-[#172D28]">Complaint Registered Successfully</h2>
            <p className="text-xs text-[#52605B]">Your facility request has been recorded into the live campus ledger.</p>
          </div>

          <div className="p-5 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] max-w-sm mx-auto">
            <span className="text-[11px] font-semibold text-[#52605B] uppercase tracking-wider block">
              Official Complaint Token
            </span>
            <span className="text-2xl font-mono font-bold text-[#203A32] mt-1 block">
              {successResult.token}
            </span>
            {successResult.category && (
              <span className="text-xs text-[#52605B] mt-1 block">
                Category: <strong>{successResult.category}</strong>
              </span>
            )}
          </div>

          <p className="text-xs text-[#52605B] max-w-md mx-auto leading-relaxed">
            Your request has been routed to the maintenance engineering squad. An inspection technician will attend during your specified availability window.
          </p>

          <div className="flex justify-center gap-3 pt-3">
            <Button
              variant="outline"
              leftIcon={<RotateCcw className="w-4 h-4" />}
              onClick={() => {
                setSuccessResult(null);
                setTitle('');
                setDescription('');
                setSpecificCategories([]);
                setUploadedPhotoFilename(null);
                setUploadedPhotoName(null);
                setUploadedPhotoSha256(null);
              }}
            >
              Submit Another Query
            </Button>
            <Button variant="primary" onClick={() => navigate('/student/history')}>
              View in History
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // -------------------------------------------------------------------------
  // STEP 3: UNLOCKED COMPLAINT SUBMISSION FORM
  // -------------------------------------------------------------------------
  const effectiveTimeSlots = taxonomy?.time_slots?.length ? taxonomy.time_slots : APPROVED_TIME_SLOTS;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Student Identity Banner */}
      <div className="p-3.5 rounded-xl bg-white border border-[#DCE5D8] flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-[#52605B]">Locker Identity:</span>
          <span className="font-semibold text-[#172D28] font-mono">{user?.id}</span>
          <span className="text-[#A8B9A3]">•</span>
          <span className="font-medium text-[#172D28]">{user?.name}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-[#203A32] bg-[#DCE5D8]/40 px-2.5 py-1 rounded-md">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#203A32]" />
          <span>Statutory Declarations Accepted</span>
        </div>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Raise a Facility Query</h1>
        <p className="text-xs text-[#52605B] mt-1">
          Complete the hierarchical classification and campus location details below to dispatch maintenance teams.
        </p>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 1. Categorisation Card (Strict Cascading Hierarchy) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#203A32]" /> 1. Issue Classification
            </CardTitle>
            <CardDescription>
              Sequence: Message Type → Category → Subcategory → Specific Category
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Complaint Title */}
            <Input
              label="Complaint Title / Subject (Optional)"
              placeholder="e.g. Washroom Tap Leakage or Air Conditioner Cooling Defect"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              helperText="Brief summary of the defect for rapid dispatch categorization"
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Step 1: Message Type */}
              <Select
                label="Message Type"
                value={messageType}
                onChange={(e) => handleMessageTypeChange(e.target.value)}
                options={taxonomy?.message_types.map((m) => ({ value: m, label: m }))}
                required
              />

              {/* Step 2: Primary Category (Disabled until Message Type selected) */}
              <Select
                label="Primary Category (19 LPU RMS Categories)"
                value={category}
                onChange={(e) => handleCategoryChange(e.target.value)}
                disabled={!messageType}
                options={[
                  { value: '', label: '-- Select Category --' },
                  ...(taxonomy?.maintenance_categories.map((c) => ({ value: c, label: c })) || []),
                ]}
                required
              />
            </div>

            {/* Step 3: Subcategory (Disabled until Category selected) */}
            <Select
              label="Subcategory"
              value={subCategory}
              onChange={(e) => handleSubCategoryChange(e.target.value)}
              disabled={!category || availableSubCategories.length === 0}
              options={[
                { value: '', label: availableSubCategories.length > 0 ? '-- Select Subcategory --' : 'No Subcategories for this Category' },
                ...availableSubCategories.map((s) => ({ value: s, label: s })),
              ]}
            />

            {/* Step 4: Specific Category Checkboxes (Disabled until Subcategory selected) */}
            {subCategory && availableSpecificCategories.length > 0 && (
              <div className="space-y-2 pt-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#172D28]">
                  Specific Issue Checklists (Select all that apply)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 rounded-lg border border-[#DCE5D8] bg-[#F5F7F2]/40 max-h-48 overflow-y-auto">
                  {availableSpecificCategories.map((item) => (
                    <label
                      key={item}
                      className="flex items-center gap-2 text-xs text-[#172D28] cursor-pointer hover:text-[#203A32]"
                    >
                      <input
                        type="checkbox"
                        checked={specificCategories.includes(item)}
                        onChange={() => toggleSpecificCategory(item)}
                        className="rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
                      />
                      <span>{item}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 2. Location & Contact Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#203A32]" /> 2. Location & Inspection Availability
            </CardTitle>
            <CardDescription>Specify campus coordinates and inspection window</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Select
                label="Campus Building / Block"
                value={building}
                onChange={(e) => setBuilding(e.target.value)}
                options={taxonomy?.campus_blocks.map((b) => ({ value: b, label: b }))}
                required
              />

              <Select
                label="Sub Block / Wing"
                value={subBlock}
                onChange={(e) => setSubBlock(e.target.value)}
                options={[
                  { value: '', label: 'None / General Wing' },
                  ...(taxonomy?.campus_sub_blocks.map((s) => ({ value: s, label: `Sub Block ${s}` })) || []),
                ]}
              />

              <Select
                label="Location Type"
                value={roomType}
                onChange={(e) => setRoomType(e.target.value)}
                options={[
                  { value: 'Room No', label: 'Room Number' },
                  { value: 'Any Other', label: 'Common Area / Other' },
                ]}
                required
              />
            </div>

            {roomType === 'Room No' ? (
              <Input
                label="Room Number"
                placeholder="e.g. 204 or Ground Floor Lab 3"
                value={roomNumber}
                onChange={(e) => setRoomNumber(e.target.value)}
                required
              />
            ) : (
              <Input
                label="Specific Location Details"
                placeholder="e.g. 3rd Floor East Washroom near Staircase B"
                value={specifiedLocation}
                onChange={(e) => setSpecifiedLocation(e.target.value)}
                required
              />
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <Input
                label="Contact Number"
                placeholder="10-digit mobile number"
                value={contactNumber}
                onChange={(e) => setContactNumber(e.target.value)}
                leftIcon={<Phone className="w-4 h-4" />}
                helperText="Must be a valid 10-digit phone number"
                required
              />

              <Input
                label="Inspection Date"
                type="date"
                value={availabilityDate}
                onChange={(e) => setAvailabilityDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                leftIcon={<Calendar className="w-4 h-4" />}
                required
              />

              <Select
                label="Availability Time Slot"
                value={timeSlot}
                onChange={(e) => setTimeSlot(e.target.value)}
                options={effectiveTimeSlots.map((t) => ({ value: t, label: t }))}
                required
              />
            </div>
          </CardContent>
        </Card>

        {/* 3. Description & Photo Attachment */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#203A32]" /> 3. Problem Description & Evidence
            </CardTitle>
            <CardDescription>Provide comprehensive details for repair teams</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Textarea
                label="Detailed Problem Description"
                placeholder="Describe the issue clearly (e.g. sparking socket, leaking tap, water overflow)..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={500}
                showCount
                rows={4}
                required
              />
              <div className="flex justify-between items-center text-[11px] text-[#52605B] mt-1">
                <span>Minimum 5 characters required</span>
                <span className={description.length >= 480 ? 'text-amber-600 font-semibold' : ''}>
                  {description.length} / 500 characters
                </span>
              </div>
            </div>

            {/* Photo Attachment */}
            <div className="p-4 rounded-xl border border-dashed border-[#DCE5D8] bg-[#F5F7F2]/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#172D28] flex items-center gap-1.5">
                  <ImageIcon className="w-4 h-4 text-[#A8B9A3]" /> Optional Damage Photo Attachment
                </span>
                <span className="text-[10px] text-[#52605B]">Max 10MB • PNG, JPEG, JPG</span>
              </div>

              {uploadedPhotoName ? (
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                  <span className="flex items-center gap-1.5 font-medium">
                    <Check className="w-4 h-4 text-emerald-600" /> {uploadedPhotoName}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setUploadedPhotoName(null);
                      setUploadedPhotoFilename(null);
                      setUploadedPhotoSha256(null);
                    }}
                    className="text-xs font-medium text-emerald-800 hover:text-emerald-950 underline"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <label className="flex flex-col items-center justify-center p-3 rounded-lg border border-[#DCE5D8] bg-white hover:border-[#203A32] cursor-pointer transition-colors text-center">
                  <Upload className="w-5 h-5 text-[#A8B9A3] mb-1" />
                  <span className="text-xs font-medium text-[#172D28]">
                    {uploadingPhoto ? 'Validating and uploading...' : 'Click to attach damage photo'}
                  </span>
                  <input
                    type="file"
                    accept="image/png, image/jpeg, image/jpg"
                    className="hidden"
                    onChange={handlePhotoUpload}
                    disabled={uploadingPhoto}
                  />
                </label>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Submit Action */}
        <div className="flex justify-end gap-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={submitting}
            leftIcon={<Send className="w-4 h-4" />}
          >
            Submit Facility Query
          </Button>
        </div>
      </form>
    </div>
  );
};
